const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/ui-home004');
const secret = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json')));
const kdCreds = JSON.parse(fs.readFileSync(path.join(root, '.local/kd-access001/dev-credentials.json')));

const PORT = process.env.PORT || 19689;
const DB = process.env.DB || 'tp_tanphat_home004_20261110';
const SHOT_DIR = process.env.SHOT_DIR || 'shots';
const shots = path.join(local, SHOT_DIR);
fs.mkdirSync(shots, { recursive: true });
const BASE_URL = `http://127.0.0.1:${PORT}`;

async function login(page, user, password) {
    await page.goto(`${BASE_URL}/web/login?db=${DB}`);
    await page.locator('[name=login]').fill(user);
    await page.locator('[name=password]').fill(password);
    await page.locator('button[type=submit]').click();
    await page.locator('.o_web_client').waitFor({ timeout: 60000 });
}

(async () => {
    console.log(`=== Starting Playwright Browser Verification for UI-HOME-004 on port ${PORT} (${DB}) ===`);
    const browser = await chromium.launch({ headless: true });
    let ok = false;
    const errors = [];

    try {
        // -------------------------------------------------------------
        // PART 1: ADMIN ROLE VERIFICATION
        // -------------------------------------------------------------
        console.log("\n[1/2] Verifying System Administrator (admin)...");
        const contextAdmin = await browser.newContext({
            viewport: { width: 1440, height: 900 },
        });
        const page = await contextAdmin.newPage();

        console.log("  Logging in as admin...");
        await login(page, 'admin', secret.admin);

        console.log("  Navigating to Home launcher...");
        await page.goto(`${BASE_URL}/odoo`);
        await page.locator('.o_web_client').waitFor({ timeout: 30000 });

        // Verify #tp-admin-home-design exists
        const adminDesign = page.locator('#tp-admin-home-design');
        await adminDesign.waitFor({ state: 'visible', timeout: 30000 });
        console.log("  ✓ Admin layout #tp-admin-home-design is visible.");

        // F-HOME-01: Verify SINGLE navbar (no duplicate internal .tp-nav)
        const internalNavbarCount = await page.locator('#tp-admin-home-design .tp-nav').count();
        console.log(`  ✓ Internal .tp-nav count: ${internalNavbarCount} (must be 0)`);
        assert.equal(internalNavbarCount, 0, 'Internal duplicate .tp-nav must NOT exist in #tp-admin-home-design');

        const nativeNavbar = page.locator('.o_main_navbar');
        await nativeNavbar.waitFor({ state: 'visible' });
        console.log("  ✓ Native Odoo navbar (.o_main_navbar) is visible and preserved.");

        const mainTitle = await page.locator('#tp-admin-home-design h1').innerText();
        const subtitle = await page.locator('#tp-admin-home-design .tp-subtitle').innerText();
        console.log(`  ✓ Title: "${mainTitle}", Subtitle: "${subtitle}"`);
        assert.equal(mainTitle, 'Trang chủ quản trị');
        assert(subtitle.includes('TANPHAT ONE'), 'Subtitle must mention TANPHAT ONE');

        // F-HOME-02: Verify 3 admin tools next to heading
        const adminTools = page.locator('.tp-admin-tools [data-tool]');
        const toolsCount = await adminTools.count();
        console.log(`  ✓ Admin tools count: ${toolsCount} (must be 3)`);
        assert.equal(toolsCount, 3, 'Must have exactly 3 admin tools');

        const toolLabels = await adminTools.locator('.tp-tool-label, span').allInnerTexts();
        console.log("  ✓ Admin tools labels:", toolLabels);
        assert(toolLabels.some((l) => l.includes('Tất cả ứng dụng')), 'Must have Tất cả ứng dụng');
        assert(toolLabels.some((l) => l.includes('Cài đặt')), 'Must have Cài đặt');
        assert(toolLabels.some((l) => l.includes('Quản lý ứng dụng')), 'Must have Quản lý ứng dụng');

        // Test panel toggle via "Tất cả ứng dụng"
        console.log("  Testing 'Tất cả ứng dụng' panel toggle...");
        const allAppsBtn = page.locator('.tp-admin-tools [data-tool="all-apps"]');
        assert.equal(await page.locator('#tp_home_all_apps').count(), 0, 'Panel must start closed');
        await allAppsBtn.click();
        await page.locator('#tp_home_all_apps').waitFor({ state: 'visible', timeout: 5000 });
        console.log("  ✓ Panel #tp_home_all_apps opened successfully.");
        await page.screenshot({ path: path.join(shots, 'admin-panel-open.png'), fullPage: false });
        console.log("  ✓ Saved screenshot: admin-panel-open.png");

        // Test panel search
        const panelSearchInput = page.locator('#tp_home_all_apps .o_tp_web_home_search_input');
        await panelSearchInput.fill('Cài đặt');
        await page.waitForTimeout(300);
        const filteredApps = await page.locator('#tp_home_all_apps .o_tp_web_home_app:visible').count();
        console.log(`  ✓ Filtered apps count for 'Cài đặt': ${filteredApps}`);
        assert(filteredApps >= 1, 'Search inside panel must find matching apps');

        // Close panel
        await page.locator('#tp_home_all_apps .o_tp_web_home_panel_close').click();
        await page.locator('#tp_home_all_apps').waitFor({ state: 'detached', timeout: 5000 });
        console.log("  ✓ Panel closed successfully.");

        // Check sections: exactly 2 sections
        const deptTitle = await page.locator('#tp-dept-title').innerText();
        const hrTitle = await page.locator('#tp-hr-title').innerText();
        console.log(`  ✓ Section 1: "${deptTitle}", Section 2: "${hrTitle}"`);
        assert.equal(deptTitle, 'Phòng ban và đơn vị');
        assert.equal(hrTitle, 'Nhân sự và tuyển dụng');

        // Check 7 module buttons
        const modules = page.locator('#tp-admin-home-design [data-module]');
        const count = await modules.count();
        console.log(`  ✓ Exactly 7 module entries present: count = ${count}`);
        assert.equal(count, 7);

        const names = await modules.locator('.tp-name').allInnerTexts();
        console.log("  ✓ Module names:", names);
        assert.deepEqual(names, [
            "Kế hoạch Kinh doanh",
            "Phòng Thiết kế",
            "Phòng Kỹ Thuật",
            "Phòng BIM-QC",
            "TADIC",
            "Quản lý nhân sự",
            "Tuyển dụng"
        ]);

        // Check statuses
        const statuses = await modules.locator('.tp-badge').allInnerTexts();
        console.log("  ✓ Status badges:", statuses);
        assert.equal(statuses[0], "Đang hoạt động");
        assert.equal(statuses[1], "Đang phát triển");
        assert.equal(statuses[2], "Đang phát triển");
        assert.equal(statuses[3], "Đang phát triển");
        assert.equal(statuses[4], "Đang phát triển");
        assert.equal(statuses[5], "Triển khai tiếp theo");
        assert.equal(statuses[6], "Đang phát triển");

        // F-HOME-03: Verify 7 distinct icons and 0 circle fallbacks
        const circleFallbacks = await page.locator('#tp-admin-home-design [data-module] .tp-icon svg circle[r="10"]').count();
        console.log(`  ✓ Circle fallback count across 7 cards: ${circleFallbacks} (must be 0)`);
        assert.equal(circleFallbacks, 0, 'No module card should fall back to a circle icon');

        // Verify distinct geometry for each card
        const kdIconHasRect = await page.locator('[data-module="business"] .tp-icon svg rect[x="2"][y="7"]').count();
        assert.equal(kdIconHasRect, 1, 'Kế hoạch Kinh doanh must have briefcase icon');

        const designIconHasRuler = await page.locator('[data-module="design"] .tp-icon svg path[d*="21.3"]').count();
        assert.equal(designIconHasRuler, 1, 'Phòng Thiết kế must have drafting ruler icon');

        const techIconHasHardhat = await page.locator('[data-module="technical"] .tp-icon svg path[d*="18a1"]').count();
        assert.equal(techIconHasHardhat, 1, 'Phòng Kỹ Thuật must have hardhat icon');

        const bimIconHasBoxes = await page.locator('[data-module="bim"] .tp-icon svg path[d*="12.92"]').count();
        assert.equal(bimIconHasBoxes, 1, 'Phòng BIM-QC must have 3D boxes icon');

        const tadicIconHasBuilding = await page.locator('[data-module="tadic"] .tp-icon svg rect[x="4"][y="2"]').count();
        assert.equal(tadicIconHasBuilding, 1, 'TADIC must have building icon');

        const hrIconHasUsers = await page.locator('[data-module="hr"] .tp-icon svg circle[cx="10"]').count();
        assert.equal(hrIconHasUsers, 1, 'Quản lý nhân sự must have users icon');

        const recruitIconHasUserPlus = await page.locator('[data-module="recruitment"] .tp-icon svg line[x1="19"]').count();
        assert.equal(recruitIconHasUserPlus, 1, 'Tuyển dụng must have user-plus icon');
        console.log("  ✓ All 7 module cards have correct, distinct SVG geometries.");

        // Check desktop featured card span
        const kdCard = page.locator('[data-module="business"]');
        const kdClasses = await kdCard.getAttribute('class');
        assert(kdClasses.includes('tp-featured'), 'KH-KD card must have tp-featured class');

        // Desktop screenshot
        await page.screenshot({ path: path.join(shots, 'admin-1440-desktop.png'), fullPage: false });
        console.log("  ✓ Saved screenshot: admin-1440-desktop.png");

        // Responsive: Tablet (768px)
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(shots, 'admin-768-tablet.png'), fullPage: false });
        console.log("  ✓ Saved screenshot: admin-768-tablet.png");

        // Responsive: Mobile (390px)
        await page.setViewportSize({ width: 390, height: 844 });
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(shots, 'admin-390-mobile.png'), fullPage: false });
        console.log("  ✓ Saved screenshot: admin-390-mobile.png");

        // Responsive: Narrow (320px) - check horizontal overflow
        await page.setViewportSize({ width: 320, height: 600 });
        await page.waitForTimeout(500);
        const hasOverflow = await page.evaluate(() => {
            return document.documentElement.scrollWidth > document.documentElement.clientWidth;
        });
        assert(!hasOverflow, 'No horizontal overflow on 320px');
        await page.screenshot({ path: path.join(shots, 'admin-320-narrow.png'), fullPage: false });
        console.log("  ✓ Saved screenshot: admin-320-narrow.png (no horizontal overflow)");

        // Reset to 1440
        await page.setViewportSize({ width: 1440, height: 900 });

        // Test Interactions: Click Placeholders
        console.log("  Testing placeholder navigation...");

        // 1. Design placeholder
        await page.locator('[data-module="design"]').click();
        await page.locator('[data-detail]').waitFor({ state: 'visible' });
        assert.equal(await page.locator('[data-detail-title]').innerText(), 'Phòng Thiết kế');
        assert.equal(await page.locator('[data-detail-status]').innerText(), 'Đang phát triển');
        assert.equal(await page.locator('[data-detail-copy]').innerText(), 'Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.');
        assert(page.url().includes('#unit=design'), 'Hash must be #unit=design');
        await page.screenshot({ path: path.join(shots, 'admin-placeholder-design.png') });
        console.log("  ✓ Phòng Thiết kế placeholder verified. Screenshot saved.");

        // Click Back
        await page.locator('[data-back]').click();
        await page.locator('#tp-admin-home-design [data-home]').waitFor({ state: 'visible' });
        assert(!page.url().includes('unit='), 'Hash cleared on Back');
        console.log("  ✓ Back to Home verified.");

        // 2. Technical placeholder
        await page.locator('[data-module="technical"]').click();
        await page.locator('[data-detail]').waitFor({ state: 'visible' });
        assert.equal(await page.locator('[data-detail-title]').innerText(), 'Phòng Kỹ Thuật');
        await page.screenshot({ path: path.join(shots, 'admin-placeholder-technical.png') });
        await page.locator('[data-back]').click();
        await page.locator('#tp-admin-home-design [data-home]').waitFor({ state: 'visible' });
        console.log("  ✓ Phòng Kỹ Thuật placeholder verified.");

        // 3. BIM-QC placeholder
        await page.locator('[data-module="bim"]').click();
        await page.locator('[data-detail]').waitFor({ state: 'visible' });
        assert.equal(await page.locator('[data-detail-title]').innerText(), 'Phòng BIM-QC');
        await page.screenshot({ path: path.join(shots, 'admin-placeholder-bim.png') });
        await page.locator('[data-back]').click();
        await page.locator('#tp-admin-home-design [data-home]').waitFor({ state: 'visible' });
        console.log("  ✓ Phòng BIM-QC placeholder verified.");

        // 4. TADIC placeholder
        await page.locator('[data-module="tadic"]').click();
        await page.locator('[data-detail]').waitFor({ state: 'visible' });
        assert.equal(await page.locator('[data-detail-title]').innerText(), 'TADIC');
        await page.screenshot({ path: path.join(shots, 'admin-placeholder-tadic.png') });
        await page.locator('[data-back]').click();
        await page.locator('#tp-admin-home-design [data-home]').waitFor({ state: 'visible' });
        console.log("  ✓ TADIC placeholder verified.");

        // 5. Tuyển dụng placeholder
        await page.locator('[data-module="recruitment"]').click();
        await page.locator('[data-detail]').waitFor({ state: 'visible' });
        assert.equal(await page.locator('[data-detail-title]').innerText(), 'Tuyển dụng');
        await page.screenshot({ path: path.join(shots, 'admin-placeholder-recruitment.png') });
        await page.locator('[data-back]').click();
        await page.locator('#tp-admin-home-design [data-home]').waitFor({ state: 'visible' });
        console.log("  ✓ Tuyển dụng placeholder verified.");

        // Test Deep-linking via Hash
        console.log("  Testing deep-link via URL hash...");
        await page.evaluate(() => { window.location.hash = '#unit=design'; });
        await page.locator('[data-detail]').waitFor({ state: 'visible', timeout: 10000 });
        assert.equal(await page.locator('[data-detail-title]').innerText(), 'Phòng Thiết kế');
        console.log("  ✓ Deep link #unit=design rendered placeholder directly.");

        // Clear hash to return Home
        await page.locator('[data-back]').click();
        await page.locator('#tp-admin-home-design [data-home]').waitFor({ state: 'visible' });
        console.log("  ✓ Returned to Home after deep link test.");

        // Test Click Quản lý nhân sự -> opens native HR module
        console.log("  Testing Quản lý nhân sự click...");
        await page.locator('[data-module="hr"]').click();
        await page.waitForTimeout(3000);
        console.log(`  ✓ Navigated after HR click. URL: ${page.url()}`);
        await page.screenshot({ path: path.join(shots, 'admin-hr-native.png') });

        // Navigate back to Home
        await page.goto(`${BASE_URL}/odoo`);
        await page.locator('#tp-admin-home-design').waitFor({ state: 'visible', timeout: 30000 });

        // Test Click KH-KD -> opens active workspace
        console.log("  Testing Kế hoạch Kinh doanh click...");
        await page.locator('[data-module="business"]').click();
        await page.waitForTimeout(3000);
        console.log(`  ✓ Navigated after KH-KD click. URL: ${page.url()}`);
        await page.screenshot({ path: path.join(shots, 'admin-business-workspace.png') });

        await contextAdmin.close();

        // -------------------------------------------------------------
        // PART 2: NON-ADMIN (THUY ANH) ROLE VERIFICATION
        // -------------------------------------------------------------
        console.log("\n[2/2] Verifying Non-Admin User (kd.thuyanh - Head of Business)...");
        const contextUser = await browser.newContext({
            viewport: { width: 1440, height: 900 },
        });
        const userPage = await contextUser.newPage();

        console.log("  Logging in as kd.thuyanh...");
        await login(userPage, 'kd.thuyanh', kdCreds.head.password);

        console.log("  Navigating to Home launcher...");
        await userPage.goto(`${BASE_URL}/odoo`);
        await userPage.locator('.o_web_client').waitFor({ timeout: 30000 });

        // Verify #tp-admin-home-design DOES NOT EXIST for non-admin
        const hasAdminLayout = await userPage.locator('#tp-admin-home-design').count();
        console.log(`  ✓ Admin layout count: ${hasAdminLayout} (must be 0)`);
        assert.equal(hasAdminLayout, 0, 'Non-admin MUST NOT see #tp-admin-home-design');

        // Verify .tp-admin-tools DOES NOT EXIST for non-admin
        const hasAdminTools = await userPage.locator('.tp-admin-tools').count();
        console.log(`  ✓ Admin tools count for non-admin: ${hasAdminTools} (must be 0)`);
        assert.equal(hasAdminTools, 0, 'Non-admin MUST NOT see .tp-admin-tools');

        // Verify UI-HOME-003 layout is rendered
        const homeInner = userPage.locator('.o_tp_web_home_inner');
        await homeInner.waitFor({ state: 'visible' });
        const userBrand = await userPage.locator('.o_tp_web_home_brand').innerText();
        const userTagline = await userPage.locator('.o_tp_web_home_tagline').innerText();
        console.log(`  ✓ Non-admin brand: "${userBrand}", Tagline: "${userTagline}"`);
        assert.equal(userBrand, 'TANPHAT ONE');
        assert.equal(userTagline, 'Trang chủ');

        // Check search input present
        const searchInput = userPage.locator('.o_tp_web_home_search_input');
        await searchInput.waitFor({ state: 'visible' });
        console.log("  ✓ Search input present for non-admin.");

        // Check groups
        const groupTitles = await userPage.locator('.o_tp_web_home_group_title').allInnerTexts();
        console.log("  ✓ Group titles for non-admin:", groupTitles);
        assert(groupTitles.includes('Không gian làm việc'), 'Must have Không gian làm việc');
        assert(groupTitles.includes('Công cụ cá nhân'), 'Must have Công cụ cá nhân');

        // Check tiles
        const tiles = await userPage.locator('.o_tp_web_home_tile .o_tp_web_home_label').allInnerTexts();
        console.log("  ✓ Tiles on non-admin Home:", tiles);
        assert(tiles.includes('Kế hoạch Kinh doanh'), 'Must have Kế hoạch Kinh doanh');

        // Check non-admin cannot access admin panel toggle
        const panelToggleCount = await userPage.locator('.o_tp_web_home_panel_toggle').count();
        assert.equal(panelToggleCount, 0, 'Non-admin has no panel toggle');

        // Screenshot non-admin Home
        await userPage.screenshot({ path: path.join(shots, 'thuyanh-ui-home-003.png'), fullPage: false });
        console.log("  ✓ Saved screenshot: thuyanh-ui-home-003.png");

        // Click KH-KD
        console.log("  Testing non-admin click on KH-KD...");
        await userPage.locator('.o_tp_web_home_tile', { hasText: 'Kế hoạch Kinh doanh' }).click();
        await userPage.waitForTimeout(2000);
        console.log(`  ✓ Navigated to workspace URL: ${userPage.url()}`);
        await userPage.screenshot({ path: path.join(shots, 'thuyanh-kd-workspace.png') });

        await contextUser.close();

        ok = true;
        console.log("\n=== ALL PLAYWRIGHT BROWSER VERIFICATIONS PASSED 100% ===");
    } catch (err) {
        console.error("Playwright verification error:", err);
        errors.push(String(err));
        throw err;
    } finally {
        await browser.close();
        let treeHashes = {};
        try {
            treeHashes = JSON.parse(fs.readFileSync(path.join(local, 'tested-source.json')));
        } catch {
            // ignore
        }
        fs.writeFileSync(path.join(shots, 'result.json'), JSON.stringify({ ok, errors, source_hashes: treeHashes }, null, 2));
    }
})();