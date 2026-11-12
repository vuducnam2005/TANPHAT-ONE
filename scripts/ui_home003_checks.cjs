/* UI-HOME-003 acceptance H01–H10, called by ui_home003_ui.cjs (clone after / dev verify).
 * Dev verify is read-only: no form edits, no route mocks, no fixture users, no Settings/Apps clicks.
 * Baselines: clone → shots/clone-before, dev → shots/dev-before (both captured before the change). */
const fs = require('node:fs');
const path = require('node:path');

const KD = 'tp_kd_workspace.menu_kd';
const PERSONAL = ['project_todo.menu_todo_todos', 'calendar.mail_menu_calendar', 'mail.menu_root_discuss'];
const SETTINGS = 'base.menu_administration';
const APPS = 'base.menu_management';
const SYSTEM_ACTORS = new Set(['admin', 'manager']);

module.exports = async function (c) {
    const { browser, login, base, db, out, local, target, check, watch, home, shot, inventory, actors, chromium } = c;
    const clone = target === 'clone';
    const baselineDir = path.join(local, 'shots', clone ? 'clone-before' : 'dev-before');
    const baseline = name => JSON.parse(fs.readFileSync(path.join(baselineDir, name)));
    const current = name => JSON.parse(fs.readFileSync(path.join(out, name)));
    const entry = id => `.o_tp_web_home_tile[data-menu-xmlid="${id}"]`;
    const search = '.o_tp_web_home_header .o_tp_web_home_search_input';
    const toggle = '.o_tp_web_home_panel_toggle';
    const panel = '#tp_home_all_apps';
    const panelInput = '.o_tp_web_home_panel_input';
    const pathOf = href => new URL(href, base).pathname;
    const ids = (page, selector) => page.locator(selector).evaluateAll(els => els.map(el => el.dataset.menuXmlid || el.dataset.entry));
    const focused = (page, selector) => page.locator(selector).evaluate(el => el === document.activeElement);
    const menuPath = m => `/odoo/${m.actionPath || 'action-' + m.actionID}`;
    function rootMenu(menus, xmlid) {
        return menus.root.children.map(id => menus[id]).find(m => m.xmlid === xmlid);
    }
    function canonicalMenus(menus) {
        return JSON.stringify(Object.entries(menus).map(([id, m]) => [
            id, m.xmlid, m.name, m.actionID, m.actionModel, m.actionPath, m.appID, m.webIcon, m.webIconData, m.children,
        ]).sort((a, b) => String(a[0]).localeCompare(String(b[0]))));
    }
    async function leftHome(page) {
        // Window actions render .o_action; some client actions (Discuss) render their own root.
        await page.waitForFunction(() => !document.querySelector('.o_tp_web_home')
            && document.querySelector('.o_action_manager > .o_action, .o_action_manager .o-mail-Discuss'), null, { timeout: 30000 });
        await page.waitForTimeout(150);
    }
    async function ready(page) {
        await page.locator('.o_tp_web_home[data-state=ready]').waitFor({ timeout: 30000 });
        await page.waitForTimeout(100);
    }
    async function backHome(page) {
        await page.locator('.o_tp_web_home_button').click();
        await ready(page);
    }

    // H01, H04, H05 (gate), H06 (note): per-actor Home content against the pre-change baseline.
    const actorList = ['admin', 'kd', ...(clone ? ['employee', 'hrinvoice', 'salesmgr', 'manager'] : [])];
    for (const actor of actorList) {
        const context = await login(browser, actor);
        const page = await context.newPage();
        watch(page);
        await home(page);
        await ready(page);
        const items = await inventory(page);
        const groups = await page.locator('.o_tp_web_home_group').evaluateAll(els => els.map(el => el.dataset.group));
        const before = baseline(`${actor}-inventory.json`).filter(x => x.xmlid);
        const beforeHref = new Map(before.map(x => [x.xmlid, x.href]));
        check(`H06 ${actor}: menu payload unchanged (switcher keeps every app)`,
            canonicalMenus(current(`${actor}-menus.json`)) === canonicalMenus(baseline(`${actor}-menus.json`)));
        const menuEntries = items.filter(x => x.xmlid);
        check(`H01 ${actor}: Home entries reuse existing menus and actions`,
            menuEntries.every(x => beforeHref.get(x.xmlid) === x.href), menuEntries);
        check(`H01 ${actor}: unique entries`, new Set(menuEntries.map(x => x.xmlid)).size === menuEntries.length);
        check(`H01 ${actor}: no business grid`, groups.every(g => ['workspace', 'personal', 'system'].includes(g)), groups);
        const text = await page.locator('.o_tp_web_home').innerText();
        check(`H01 ${actor}: no placeholder or KPI`, !/sắp ra mắt|coming soon|\bKPI\b|doanh thu|công nợ/i.test(text));
        const hasKd = beforeHref.has(KD);
        check(`H01/H04 ${actor}: workspace shown only with its menu`,
            hasKd === menuEntries.some(x => x.xmlid === KD) && hasKd === (groups[0] === 'workspace'), groups);
        const personal = PERSONAL.filter(x => beforeHref.has(x));
        check(`H01 ${actor}: personal tools in order`,
            JSON.stringify(items.filter(x => x.group === 'personal').map(x => x.xmlid)) === JSON.stringify(personal));
        const system = SYSTEM_ACTORS.has(actor);
        check(`H05 ${actor}: administration only for base.group_system`,
            system === groups.includes('system') && system === (await page.locator(toggle).count() === 1), groups);
        if (system) {
            const expected = ['all-apps', ...[SETTINGS, APPS].filter(x => beforeHref.has(x))];
            check(`H05 ${actor}: Tất cả ứng dụng, Cài đặt, Quản lý ứng dụng`,
                JSON.stringify(await ids(page, '[data-group=system] .o_tp_web_home_tile')) === JSON.stringify(expected));
            check(`H05 ${actor}: system labels`, JSON.stringify(await page.locator('[data-group=system] .o_tp_web_home_label').allTextContents())
                === JSON.stringify(['Tất cả ứng dụng', 'Cài đặt', 'Quản lý ứng dụng'].slice(0, expected.length)));
        }
        const others = before.filter(x => !menuEntries.some(y => y.xmlid === x.xmlid));
        check(`H06 ${actor}: switcher note iff other apps`,
            (await page.locator('.o_tp_web_home_note').count() === 1) === (others.length > 0 && menuEntries.length > 0), others.length);
        if (!hasKd) {
            await page.locator(search).fill('khkd');
            await page.locator('.o_tp_web_home_empty[data-empty=search]').waitFor();
            const url = page.url();
            await page.locator(search).press('Enter');
            await page.waitForTimeout(400);
            check(`H04 ${actor}: khkd finds nothing; Enter stays on Home`,
                page.url() === url && await page.locator('.o_tp_web_home').count() === 1);
            await page.locator(search).fill(''); await page.waitForTimeout(80);
        }
        if (!system) {
            for (const query of ['cai dat', 'settings', 'quan ly ung dung', 'tat ca ung dung', 'apps']) {
                await page.locator(search).fill(query);
                await page.waitForTimeout(60);
                check(`H05 ${actor}: '${query}' never reaches hidden admin entries`, await page.locator('.o_tp_web_home_tile').count() === 0);
            }
            const url = page.url();
            await page.locator(search).press('Enter');
            await page.waitForTimeout(400);
            check(`H07 ${actor}: Enter on a hidden admin query does not navigate`,
                page.url() === url && await page.locator('.o_tp_web_home').count() === 1 && await page.locator(panel).count() === 0);
            await page.locator(search).fill(''); await page.waitForTimeout(80);
        }
        await shot(page, `${actor}-home-1440`);
        await context.close();
    }

    // H02/H03: KH-KD workspace and its reused destinations, opened from the new card.
    {
        const after = current('kd-destinations.json');
        const before = baseline('kd-destinations.json');
        check('H03 KH-KD sidebar unchanged', JSON.stringify(after.leaves) === JSON.stringify(before.leaves), after.leaves);
        const strip = d => d.destinations.map(x => [x.label, x.href, x.url, x.title, x.total, x.rows]);
        check('H03 KH-KD destinations, titles and totals unchanged', JSON.stringify(strip(after)) === JSON.stringify(strip(before)), strip(after));
        check('H03 KH-KD has no HR or invoice entry', !after.leaves.some(x => /nhân sự|hóa đơn|employee|invoic/i.test(x.label)));
    }
    {
        const context = await login(browser, 'kd');
        const page = await context.newPage();
        watch(page);
        await page.goto(`${base}/odoo`);
        await page.locator(entry(KD)).waitFor({ timeout: 30000 });
        check('H10 /odoo opens Home as default app', await page.locator('.o_tp_web_home').count() === 1, page.url());
        const href = await page.locator(entry(KD)).getAttribute('href');
        const tab = context.waitForEvent('page');
        await page.locator(entry(KD)).click({ modifiers: ['Control'] });
        const opened = await tab;
        await opened.waitForLoadState();
        await opened.locator('.o_tp_kd_ov').waitFor({ timeout: 30000 });
        check('H02 Ctrl-click KH-KD opens a native new tab', pathOf(opened.url()).startsWith(href), opened.url());
        await opened.close();
        check('H02 Ctrl-click keeps Home in place', await page.locator('.o_tp_web_home').count() === 1);
        await page.locator(entry(KD)).click();
        await page.locator('.o_tp_kd_ov').waitFor({ timeout: 30000 });
        check('H02 card opens the KH-KD overview', pathOf(page.url()).startsWith(href), page.url());
        await shot(page, 'kd-workspace-from-home');
        await page.goBack();
        await page.locator(entry(KD)).waitFor({ timeout: 30000 });
        check('H10 Back returns to Home', await page.locator('.o_tp_web_home').count() === 1);
        await page.goForward();
        await page.locator('.o_tp_kd_ov').waitFor({ timeout: 30000 });
        await page.reload();
        await page.locator('.o_tp_kd_ov').waitFor({ timeout: 30000 });
        check('H10 refresh keeps the KH-KD deep link', pathOf(page.url()).startsWith(href), page.url());
        await backHome(page);
        check('H10 Home button returns to /odoo/tp-home', pathOf(page.url()) === '/odoo/tp-home', page.url());
        await page.locator(search).focus();
        await page.keyboard.press('Tab');
        check('H07 keyboard reaches the KH-KD card first', await page.evaluate(() => document.activeElement?.dataset.menuXmlid) === KD);
        const expectations = {
            khkd: [KD], 'kế hoạch': [KD], 'KE HOACH KINH DOANH': [KD], 'kh-kd': [KD],
            lich: [PERSONAL[1]], 'lịch làm việc': [PERSONAL[1]], chat: [PERSONAL[2]], 'trao doi': [PERSONAL[2]],
            todo: [PERSONAL[0]], 'viec ca nhan': [PERSONAL[0]],
            crm: [], 'hop dong': [], 'tp contracts': [], 'nhan su': [], 'hoa don': [], 'cai dat': [],
        };
        for (const [query, expected] of Object.entries(expectations)) {
            await page.locator(search).fill(query);
            await page.waitForTimeout(60);
            const found = await ids(page, '.o_tp_web_home_tile');
            check(`H07 search '${query}'`, JSON.stringify(found) === JSON.stringify(expected), found);
        }
        await page.locator(search).fill('crm'); await page.waitForTimeout(80);
        check('H07 empty search state', await page.locator('.o_tp_web_home_empty[data-empty=search] .o_tp_web_home_empty_title').innerText()
            === 'Không có lối vào phù hợp trên Trang chủ');
        await shot(page, 'kd-search-empty');
        await page.locator('.o_tp_web_home_empty button').click();
        await page.waitForFunction(() => document.querySelectorAll('.o_tp_web_home_tile').length > 0, null, { timeout: 5000 }).catch(() => {});
        const restored = { value: await page.locator(search).inputValue(), tiles: await page.locator('.o_tp_web_home_tile').count(),
            focused: await focused(page, search) };
        check('H07 clear restores Home and keeps focus in search', restored.value === '' && restored.tiles === 4 && restored.focused, restored);
        await page.locator(search).fill('lich');
        await page.locator(search).press('Escape');
        await page.waitForTimeout(100);
        check('H07 Escape clears the search and stays on Home',
            await page.locator(search).inputValue() === '' && await page.locator('.o_tp_web_home').count() === 1);
        await page.locator(search).fill('ke hoach');
        await page.locator(search).evaluate(el => {
            el.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
            el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', isComposing: true, bubbles: true }));
        });
        await page.waitForTimeout(300);
        check('H07 IME Enter is ignored', await page.locator('.o_tp_web_home').count() === 1);
        await page.locator(search).evaluate(el => el.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true })));
        await page.locator(search).press('Enter');
        await page.locator('.o_tp_kd_ov').waitFor({ timeout: 30000 });
        check('H07 Enter opens the first displayed result (KH-KD)', pathOf(page.url()).startsWith(href), page.url());
        await backHome(page);
        for (const id of PERSONAL) {
            const destination = await page.locator(entry(id)).getAttribute('href');
            await page.locator(entry(id)).click();
            await leftHome(page);
            check(`H01 personal tool ${id} opens its native app`, pathOf(page.url()).startsWith(destination), page.url());
            check(`H09 ${id}: no Home style leak`, await page.locator('.o_action_manager').evaluate(el => !getComputedStyle(el).getPropertyValue('--tp-home-bg').trim()));
            await backHome(page);
        }
        await context.close();
    }

    // H05/H07: administrators' in-page panel, its own search, Escape and focus return.
    {
        const context = await login(browser, 'admin');
        const page = await context.newPage();
        watch(page);
        await home(page);
        await ready(page);
        const before = baseline('admin-inventory.json').filter(x => x.xmlid);
        check('H05 panel closed by default', await page.locator(panel).count() === 0 && await page.locator(toggle).getAttribute('aria-expanded') === 'false');
        await page.locator(toggle).click();
        await page.locator(panel).waitFor();
        await page.waitForTimeout(250);
        check('H05 panel opens with focus in its search', await focused(page, panelInput) && await page.locator(toggle).getAttribute('aria-expanded') === 'true');
        const listed = await page.locator('.o_tp_web_home_app').evaluateAll(els => els.map(el => `${el.dataset.menuXmlid}=${el.getAttribute('href')}`));
        check("H05 panel lists exactly the user's own menus", JSON.stringify([...listed].sort()) === JSON.stringify(before.map(x => `${x.xmlid}=${x.href}`).sort()), listed);
        check('H09 panel motion within 120–200 ms', await page.locator(panel).evaluate(el => {
            const ms = parseFloat(getComputedStyle(el).animationDuration) * 1000;
            return ms >= 120 && ms <= 200;
        }));
        await shot(page, 'admin-all-apps-panel', true);
        await page.locator(panelInput).fill('hoa don');
        await page.waitForTimeout(80);
        const panelFound = await ids(page, '.o_tp_web_home_app');
        check('H05 panel search', JSON.stringify(panelFound) === JSON.stringify(['account.menu_finance']), panelFound);
        await page.locator(panelInput).press('Escape');
        await page.waitForTimeout(100);
        check('H07 first Escape clears the panel search', await page.locator(panelInput).inputValue() === '' && await page.locator(panel).count() === 1);
        await page.locator(panelInput).press('Escape');
        await page.waitForTimeout(150);
        check('H07 second Escape closes the panel, focus back on its toggle, Home kept',
            await page.locator(panel).count() === 0 && await focused(page, toggle) && await page.locator('.o_tp_web_home').count() === 1);
        await page.keyboard.press('Enter');
        await page.locator(panel).waitFor();
        await page.locator('.o_tp_web_home_panel_close').click();
        await page.waitForTimeout(100);
        check('H05 close button returns focus to the toggle', await page.locator(panel).count() === 0 && await focused(page, toggle));
        await page.locator(search).fill('cai dat'); await page.waitForTimeout(80);
        check('H05 admin main search finds Cài đặt', (await ids(page, '.o_tp_web_home_tile')).includes(SETTINGS));
        await page.locator(search).fill('hoa don'); await page.waitForTimeout(80);
        check('H05 main search never lists panel-only apps', await page.locator('.o_tp_web_home_tile').count() === 0);
        await page.locator(search).fill(''); await page.waitForTimeout(80);
        await page.locator(toggle).click();
        await page.locator(panelInput).fill('hoa don'); await page.waitForTimeout(80);
        await page.locator(panelInput).press('Enter');
        await leftHome(page);
        const invoice = before.find(x => x.xmlid === 'account.menu_finance').href;
        check('H05 panel Enter opens Hóa đơn', pathOf(page.url()).startsWith(invoice), page.url());
        check('H09 no Home style leak after the panel', await page.locator('.o_action_manager').evaluate(el => !getComputedStyle(el).getPropertyValue('--tp-home-bg').trim()));
        await backHome(page);
        check('H05 reload after navigation closes the panel', await page.locator(panel).count() === 0);
        if (clone) {
            for (const id of [SETTINGS, APPS]) {
                const destination = await page.locator(entry(id)).getAttribute('href');
                await page.locator(entry(id)).click();
                await leftHome(page);
                check(`H05 ${id} opens its native page`, pathOf(page.url()).startsWith(destination), page.url());
                await backHome(page);
            }
        }
        await context.close();
    }

    // H06: other apps stay reachable from the native switcher, desktop and phone.
    const switcherActor = clone ? 'hrinvoice' : 'kd';
    const switcherApps = clone ? ['account.menu_finance', 'hr.menu_hr_root'] : ['crm.crm_menu_root', 'contacts.menu_contacts'];
    const switcherMenus = current(`${switcherActor}-menus.json`);
    {
        const context = await login(browser, switcherActor);
        const page = await context.newPage();
        watch(page);
        await home(page);
        await ready(page);
        await page.locator('.o_navbar_apps_menu button').click();
        const dropdown = await ids(page, '.o-dropdown--menu .o_app');
        check(`H06 ${switcherActor}: desktop switcher lists every root app`,
            JSON.stringify(dropdown) === JSON.stringify(switcherMenus.root.children.map(id => switcherMenus[id].xmlid)), dropdown);
        await shot(page, `${switcherActor}-switcher-desktop`);
        await page.keyboard.press('Escape');
        for (const id of switcherApps) {
            check(`H06 ${id} is not on Home`, await page.locator(entry(id)).count() === 0);
            await page.locator('.o_navbar_apps_menu button').click();
            await page.locator(`.o-dropdown--menu .o_app[data-menu-xmlid="${id}"]`).click();
            await leftHome(page);
            check(`H06 desktop switcher opens ${id}`, pathOf(page.url()).startsWith(menuPath(rootMenu(switcherMenus, id))), page.url());
            await backHome(page);
        }
        await context.close();
    }
    {
        const context = await login(browser, switcherActor, { viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
        const page = await context.newPage();
        watch(page);
        await home(page);
        await ready(page);
        await page.locator('.o_menu_toggle').click();
        await page.locator('.o_app_menu_sidebar').waitFor();
        const item = page.locator(`.o_app_menu_sidebar li.o_app[data-menu-xmlid="${switcherApps[0]}"]`);
        if (!await item.count()) await page.locator('.o_app_menu_sidebar .o_sidebar_topbar a.btn-primary').click();
        await item.waitFor();
        await page.waitForTimeout(250);
        await shot(page, `${switcherActor}-switcher-mobile-390`);
        await item.click();
        await leftHome(page);
        check(`H06 phone switcher (☰ → All Apps) opens ${switcherApps[0]}`,
            pathOf(page.url()).startsWith(menuPath(rootMenu(switcherMenus, switcherApps[0]))), page.url());
        await context.close();
    }

    // H09: responsive layout, targets, motion, reduced motion and real browser zoom.
    for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
        const small = width < 768;
        for (const actor of ['admin', 'kd']) {
            const context = await login(browser, actor, { viewport: { width, height: small ? 844 : 900 }, hasTouch: small, isMobile: small });
            const page = await context.newPage();
            watch(page);
            await home(page);
            await ready(page);
            const geometry = () => page.evaluate(() => {
                const root = document.querySelector('.o_tp_web_home');
                const visible = [...root.querySelectorAll('a, button, input')].filter(el => el.getClientRects().length);
                const small = visible.filter(el => el.tagName !== 'INPUT' && (el.clientWidth < 44 || el.clientHeight < 44))
                    .map(el => `${el.className} ${el.clientWidth}x${el.clientHeight}`);
                return { page: document.documentElement.scrollWidth <= innerWidth, home: root.scrollWidth <= root.clientWidth + 1,
                    autofocus: document.activeElement?.tagName === 'INPUT', small,
                    inputs: [...root.querySelectorAll('input')].every(el => el.clientHeight >= 44) };
            });
            let g = await geometry();
            check(`H09 ${actor} ${width}: no horizontal overflow`, g.page && g.home, g);
            check(`H09 ${actor} ${width}: targets at least 44 px`, !g.small.length && g.inputs, g.small);
            check(`H09 ${actor} ${width}: no autofocus`, !g.autofocus);
            if (actor === 'kd') {
                check(`H09 kd ${width}: KH-KD card in the first viewport`,
                    await page.locator(entry(KD)).evaluate(el => el.getBoundingClientRect().bottom <= innerHeight));
                await shot(page, `kd-top-${width}`);
            } else {
                await page.locator(toggle).click();
                await page.locator(panel).waitFor();
                await page.waitForTimeout(250);
                g = await geometry();
                check(`H09 admin ${width}: panel open, no overflow, targets`, g.page && g.home && !g.small.length, g);
                await page.locator('.o_tp_web_home').evaluate(el => { el.scrollTop = el.scrollHeight; });
                await page.waitForTimeout(100);
                check(`H09 admin ${width}: vertical scroll reaches the panel end`,
                    await page.locator(panel).evaluate(el => el.getBoundingClientRect().bottom <= innerHeight + 2));
                await shot(page, `admin-panel-bottom-${width}`);
                await page.locator('.o_tp_web_home').evaluate(el => { el.scrollTop = 0; });
                await shot(page, `admin-top-${width}`);
            }
            await context.close();
        }
    }
    {
        const context = await login(browser, 'admin');
        const page = await context.newPage();
        await home(page);
        await ready(page);
        check('H09 motion within 120–200 ms', await page.locator('.o_tp_web_home_tile').first().evaluate(el => {
            const ms = parseFloat(getComputedStyle(el).transitionDuration) * 1000;
            return ms >= 120 && ms <= 200;
        }));
        await context.close();
        const reduced = await login(browser, 'admin', { reducedMotion: 'reduce' });
        const p = await reduced.newPage();
        await home(p);
        await ready(p);
        await p.locator(toggle).click();
        await p.locator(panel).waitFor();
        check('H09 reduced motion removes transitions and the panel animation',
            await p.locator('.o_tp_web_home_tile').first().evaluate(el => getComputedStyle(el).transitionDuration === '0s')
            && await p.locator(panel).evaluate(el => getComputedStyle(el).animationName === 'none'));
        await reduced.close();
    }

    if (clone) {
        // H08: failed fresh menu, retry, late response after unmount, user and company switch.
        {
            const context = await login(browser, 'admin');
            const page = await context.newPage();
            let requests = 0;
            await page.route('**/web/webclient/load_menus**', async route => {
                requests++;
                if (requests === 2) await route.fulfill({ status: 503, body: 'Fixture menu failure' });
                else await route.continue();
            });
            await page.goto(`${base}/odoo/tp-home`);
            await page.locator('.o_tp_web_home_error').waitFor({ timeout: 30000 });
            check('H08 failed fresh menu shows no cached entry', await page.locator('.o_tp_web_home_tile').count() === 0);
            check('H08 error differs from empty', (await page.locator('.o_tp_web_home_error').innerText()).includes('Chưa tải được Trang chủ')
                && !await page.locator('.o_tp_web_home_empty[data-empty]').count());
            await shot(page, 'menu-error');
            await page.locator('.o_tp_web_home_error button').click();
            await page.locator(entry(KD)).waitFor();
            check('H08 retry loads fresh menus', await page.locator('.o_tp_web_home[data-state=ready]').count() === 1);
            await page.unroute('**/web/webclient/load_menus**');
            await context.close();
        }
        {
            const context = await login(browser, 'admin');
            const page = await context.newPage();
            let requests = 0;
            await page.route('**/web/webclient/load_menus**', async route => {
                requests++;
                if (requests === 2) await new Promise(resolve => setTimeout(resolve, 2500));
                await route.continue().catch(() => {});
            });
            await page.goto(`${base}/odoo/tp-home`);
            await page.locator('.o_tp_web_home[data-state=loading]').waitFor({ timeout: 30000 });
            await page.locator('.o_navbar_apps_menu button').click();
            await page.locator('.o-dropdown--menu .o_app[data-menu-xmlid="mail.menu_root_discuss"]').click();
            await page.locator('.o-mail-Discuss').waitFor({ timeout: 30000 });
            await page.waitForTimeout(3000);
            check('H08 a late Home response after leaving does not bring Home back',
                await page.locator('.o-mail-Discuss').count() === 1 && !await page.locator('.o_tp_web_home').count());
            await context.close();
        }
        {
            const same = await login(browser, 'admin');
            const p = await same.newPage();
            watch(p);
            await home(p);
            await p.locator('button.o_user_menu').click();
            await p.locator('[data-menu=logout]').click();
            await p.waitForURL(/\/web\/login/);
            const auth = await same.request.post(`${base}/web/session/authenticate`, { data: { jsonrpc: '2.0', method: 'call', params: { db, ...actors.employee } } });
            check('H10 second user logs in in the same browser', Boolean((await auth.json()).result?.uid));
            await p.addInitScript(() => {
                window.__homeSeen = [];
                new MutationObserver(() => {
                    window.__homeSeen.push(...[...document.querySelectorAll('.o_tp_web_home_tile')].map(el => el.dataset.menuXmlid || el.dataset.entry));
                }).observe(document, { childList: true, subtree: true });
            });
            await home(p);
            await ready(p);
            const seen = await p.evaluate(() => window.__homeSeen);
            check('H08 cached actor: the next user never sees KH-KD or administration',
                seen.length > 0 && ![KD, SETTINGS, APPS, 'all-apps'].some(x => seen.includes(x)), [...new Set(seen)]);
            await same.close();
        }
        {
            const multi = await login(browser, 'manager');
            const m = await multi.newPage();
            watch(m);
            await home(m);
            await ready(m);
            const beforeSwitch = await ids(m, '.o_tp_web_home_tile');
            await m.locator('button.o_switch_company_menu').click();
            await m.locator('.o_switch_company_item .log_into').filter({ hasText: 'UI HOME003' }).click();
            await m.waitForTimeout(800);
            await ready(m);
            const afterSwitch = await ids(m, '.o_tp_web_home_tile');
            check('H08 company switch reloads Home with the permitted menus', JSON.stringify(afterSwitch) === JSON.stringify(beforeSwitch), afterSwitch);
            await shot(m, 'manager-company-b');
            await multi.close();
        }
        {
            const mock = await login(browser, 'admin', { viewport: { width: 360, height: 844 }, hasTouch: true, isMobile: true });
            const page = await mock.newPage();
            const longName = 'Hồ sơ khảo sát và kiểm tra công trình có tên ứng dụng rất dài';
            await page.route('**/web/webclient/load_menus**', async route => {
                const response = await route.fetch();
                const menu = await response.json();
                const contact = Object.values(menu).find(x => x.xmlid === 'contacts.menu_contacts');
                Object.assign(contact, { xmlid: 'home003.unknown_app', name: longName, webIconData: 'data:image/png;base64,broken' });
                await route.fulfill({ response, json: menu });
            });
            await home(page);
            await ready(page);
            check('H05 unknown root is not on Home', await page.locator(entry('home003.unknown_app')).count() === 0);
            await page.locator(toggle).click();
            const unknown = page.locator('.o_tp_web_home_app[data-menu-xmlid="home003.unknown_app"]');
            await unknown.locator('.o_tp_web_home_icon_monogram').waitFor();
            check('H05 unknown app keeps its native name and destination in the panel',
                (await unknown.innerText()).includes(longName) && await unknown.getAttribute('href') === '/odoo/contacts');
            check('H05 broken icon falls back to a monogram', await unknown.locator('img').count() === 0);
            check('H09 long label wraps without overflow', await unknown.evaluate(el => el.scrollWidth <= el.clientWidth + 1));
            await unknown.scrollIntoViewIfNeeded();
            await shot(page, 'unknown-long-name-panel-360');
            await mock.close();
        }
        // H10: dirty form guard and a user's own Home Action.
        {
            const context = await login(browser, 'admin');
            const page = await context.newPage();
            watch(page);
            await page.goto(`${base}/odoo/contacts`);
            await page.locator('.o_control_panel .o_list_button_add, .o_control_panel .o-kanban-button-new').first().click();
            await page.locator('.o_form_view [name=email] input').fill('unsaved.home003@example.invalid');
            const formUrl = page.url();
            await page.locator('.o_tp_web_home_button').click();
            await page.waitForTimeout(600);
            check('H10 invalid unsaved form keeps the native guard',
                page.url() === formUrl && await page.locator('.o_form_view').count() === 1 && !await page.locator('.o_tp_web_home').count());
            await shot(page, 'unsaved-native-guard');
            await context.close();
            const personal = await login(browser, 'actionuser');
            const own = await personal.newPage();
            await own.goto(`${base}/odoo`);
            await own.locator('.o-mail-Discuss').waitFor({ timeout: 30000 });
            check('H10 own Home Action stays Discuss', !await own.locator('.o_tp_web_home').count());
            await personal.close();
        }
    }

    const profile = path.join(local, `zoom-${target}`);
    const zoomContext = await chromium.launchPersistentContext(profile, { channel: 'chromium', headless: true, viewport: null, args: ['--window-size=1440,900'], locale: 'vi-VN' });
    try {
        const settings = await zoomContext.newPage();
        await settings.goto('chrome://settings/appearance');
        await settings.locator('#zoomLevel').waitFor();
        await zoomContext.request.post(`${base}/web/session/authenticate`, { data: { jsonrpc: '2.0', method: 'call', params: { db, ...actors.admin } } });
        const p = await zoomContext.newPage();
        for (const zoom of [1.25, 1.5]) {
            await settings.locator('#zoomLevel').selectOption(String(zoom));
            await home(p);
            await ready(p);
            await p.locator(toggle).click();
            await p.locator(panel).waitFor();
            const geometry = await p.evaluate(() => ({ dpr: devicePixelRatio, width: innerWidth, page: document.documentElement.scrollWidth <= innerWidth,
                home: document.querySelector('.o_tp_web_home').scrollWidth <= document.querySelector('.o_tp_web_home').clientWidth + 1 }));
            check(`H09 real zoom ${zoom * 100}%`, Math.abs(geometry.dpr - zoom) < 0.01 && geometry.page && geometry.home, geometry);
            await shot(p, `admin-zoom-${zoom * 100}`);
        }
        await settings.locator('#zoomLevel').selectOption('1');
    } finally {
        await zoomContext.close();
    }
};
