const fs = require('node:fs');
const path = require('node:path');
module.exports = async function (c) {
    const { browser, login, base, db, out, local, target, check, watch, home, shot, inventory, actors, chromium } = c;
    const tile = id => `.o_tp_web_home_tile[data-menu-xmlid="${id}"]`;
    const search = '.o_tp_web_home_search_input';
    const ids = { kd: 'tp_kd_workspace.menu_kd', projects: 'tp_project.menu_tp_projects', contracts: 'tp_contract.menu_tp_contracts', project: 'project.menu_main_pm' };
    for (const actor of ['admin', 'kd', ...(target === 'clone' ? ['employee', 'manager'] : [])]) {
        const context = await login(browser, actor);
        const page = await context.newPage();
        watch(page);
        await home(page);
        const items = await inventory(page);
        const groups = await page.locator('.o_tp_web_home_group_title').allTextContents();
        check(`${actor}: unique menus`, new Set(items.map(x => x.xmlid)).size === items.length);
        if (['admin', 'kd'].includes(actor)) {
            const before = JSON.parse(fs.readFileSync(path.join(local, 'shots/clone-before', `${actor}-inventory.json`)));
            check(`${actor}: same menu destinations`, JSON.stringify(items.map(x => `${x.xmlid}=${x.href}`).sort()) === JSON.stringify(before.map(x => `${x.xmlid}=${x.href}`).sort()));
            check(`${actor}: four groups`, groups.join('|') === 'Không gian làm việc|Công việc cá nhân|Ứng dụng nghiệp vụ|Quản trị hệ thống');
            check(`${actor}: workspace first`, items[0].xmlid === ids.kd);
            check(`${actor}: contracts description`, await page.locator(tile(ids.contracts)).innerText().then(t => t.includes('Hợp đồng và phiên bản hồ sơ')));
        } else {
            check(`${actor}: no KH-KD workspace`, !items.some(x => x.xmlid === ids.kd) && !groups.includes('Không gian làm việc'));
            check(`${actor}: only permitted tiles`, items.every(x => x.xmlid !== 'tp_contract.menu_tp_contracts'));
            await shot(page, `${actor}-desktop`);
        }
        if (actor === 'admin') {
            for (const query of ['du an', 'dự án', 'project', 'hop dong', 'contracts', 'crm', 'invoice', 'nhan su', 'hr', 'khkd', 'lich', 'todo']) {
                await page.locator(search).fill(query);
                await page.waitForTimeout(80);
                check(`search ${query}`, (await page.locator('.o_tp_web_home_tile').count()) > 0);
            }
            await page.locator(search).fill('khong co ket qua zzz');
            check('search empty message', await page.locator('.o_tp_web_home_empty_title').textContent() === 'Không tìm thấy ứng dụng phù hợp');
            await page.locator('.o_tp_web_home_empty button').click();
            await page.waitForFunction(count => document.querySelectorAll('.o_tp_web_home_tile').length === count, items.length);
            check('clear restores whole catalog', await page.locator('.o_tp_web_home_tile').count() === items.length);
            await page.locator(search).fill('crm');
            await page.locator(search).press('Escape');
            await page.waitForTimeout(80);
            check('Escape clears', await page.locator(search).inputValue() === '');
            await page.locator(search).evaluate(el => {
                el.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
                el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', isComposing: true, bubbles: true }));
            });
            check('IME Enter keeps Home', await page.locator('.o_tp_web_home').count() === 1);
            await page.locator(search).evaluate(el => el.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true })));
            await page.locator(search).press('Enter');
            await page.locator('.o_tp_kd_ov').waitFor({ timeout: 30000 });
            check('Enter opens first displayed workspace', await page.locator('.o_tp_kd_sidebar').count() > 0 || await page.locator('.o_tp_kd_ov').count() === 1);
            await page.locator('.o_tp_web_home_button').click();
            await page.locator(tile(ids.projects)).waitFor();
            for (const key of ['projects', 'contracts', 'project']) {
                const destination = await page.locator(tile(ids[key])).getAttribute('href');
                await page.locator(tile(ids[key])).click();
                await page.locator('.o_action_manager .o_view_controller').first().waitFor({ timeout: 20000 });
                check(`${key}: opens native view`, !await page.locator('.o_tp_web_home').count(), destination);
                check(`${key}: no Home style leak`, await page.locator('.o_action_manager').evaluate(el => !getComputedStyle(el).getPropertyValue('--tp-home-bg').trim()));
                await page.locator('.o_tp_web_home_button').click();
                await page.locator(tile(ids[key])).waitFor();
            }
            const newTab = context.waitForEvent('page');
            await page.locator(tile(ids.contracts)).click({ modifiers: ['Control'] });
            const opened = await newTab;
            await opened.waitForURL(/\/odoo\//);
            await opened.waitForLoadState();
            check('Ctrl-click native tab', opened.url().includes('/odoo/'));
            await opened.close();
            await page.locator(tile(ids.project)).click();
            await page.locator('.o_view_controller').first().waitFor();
            await page.goBack();
            await page.locator(tile(ids.project)).waitFor();
            await page.goForward();
            await page.locator('.o_view_controller').first().waitFor();
            check('history back/forward', !await page.locator('.o_tp_web_home').count());
            await page.reload();
            await page.locator('.o_view_controller').first().waitFor();
            check('deep link refresh retains app', !page.url().includes('tp-home'));
            await home(page);
            await page.locator(search).focus();
            await page.keyboard.press('Tab');
            check('keyboard reaches first tile', await page.evaluate(() => document.activeElement?.dataset.menuXmlid === 'tp_kd_workspace.menu_kd'));
            await page.keyboard.press('Enter');
            await page.locator('.o_tp_kd_ov').waitFor();
            check('keyboard tile opens workspace', true);
            await page.locator('.o_navbar_apps_menu button').click();
            await page.locator('.o-dropdown--menu [data-menu-xmlid="tp_web_home.menu_home"]').click();
            await page.locator(tile(ids.kd)).waitFor();
            check('native app switcher opens Home', true);
        }
        await context.close();
    }

    for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
        const context = await login(browser, 'admin', { viewport: { width, height: width < 768 ? 844 : 900 }, hasTouch: width < 768, isMobile: width < 768 });
        const page = await context.newPage();
        watch(page);
        await home(page);
        const geometry = await page.evaluate(() => {
            const home = document.querySelector('.o_tp_web_home');
            return { page: document.documentElement.scrollWidth <= innerWidth, home: home.scrollWidth <= home.clientWidth + 1,
                autofocus: document.activeElement.tagName === 'INPUT',
                targets: [...home.querySelectorAll('a')].every(el => el.clientWidth >= 44 && el.clientHeight >= 44) };
        });
        check(`${width}: no horizontal overflow`, geometry.page && geometry.home, geometry);
        check(`${width}: touch targets`, geometry.targets);
        check(`${width}: no autofocus`, !geometry.autofocus);
        if (width === 390) {
            await page.locator('.o_mobile_menu_toggle').click();
            await page.locator('.o_burger_menu').waitFor();
            await page.keyboard.press('Escape');
            await page.locator('.o_burger_menu').waitFor({ state: 'hidden' });
            await page.waitForTimeout(100);
            check('mobile native drawer Escape/focus retained', await page.locator('.o_mobile_menu_toggle').evaluate(el => el === document.activeElement));
        }
        await page.locator('.o_tp_web_home').evaluate(el => { el.scrollTop = el.scrollHeight; });
        await page.waitForTimeout(100);
        check(`${width}: can reach admin section`, await page.locator('[data-group=system]').evaluate(el => el.getBoundingClientRect().bottom <= innerHeight + 2));
        await shot(page, `admin-bottom-${width}`);
        await page.locator('.o_tp_web_home').evaluate(el => { el.scrollTop = 0; });
        await shot(page, `admin-top-${width}`);
        await context.close();
    }
    {
        const context = await login(browser, 'admin', { reducedMotion: 'reduce' });
        const page = await context.newPage();
        await home(page);
        check('reduced motion', await page.locator('.o_tp_web_home_tile').first().evaluate(el => getComputedStyle(el).transitionDuration === '0s'));
        await context.close();
    }

    if (target === 'clone') {
        const context = await login(browser, 'admin');
        const page = await context.newPage();
        // First response initializes native Odoo; the Home refresh then fails independently.
        let requests = 0;
        await page.route('**/web/webclient/load_menus', async route => {
            requests++;
            if (requests === 2) await route.fulfill({ status: 503, body: 'Fixture menu failure' });
            else await route.continue();
        });
        await page.goto(`${base}/odoo/tp-home`);
        await page.locator('.o_tp_web_home_error').waitFor();
        check('failed fresh menu hides cached tiles', await page.locator('.o_tp_web_home_tile').count() === 0);
        check('failure differs from empty', !(await page.locator('.o_tp_web_home_empty').innerText()).includes('chưa được cấp'));
        await shot(page, 'menu-error');
        await page.locator('.o_tp_web_home_error button').click();
        await page.locator(tile(ids.kd)).waitFor();
        check('retry loads menu', true);
        await page.unroute('**/web/webclient/load_menus');
        await page.goto(`${base}/odoo/contacts`);
        await page.locator('.o_control_panel .o_list_button_add, .o_control_panel .o-kanban-button-new').first().click();
        const email = page.locator('.o_form_view [name=email] input');
        await email.fill('unsaved.home002@example.invalid');
        const formUrl = page.url();
        await page.locator('.o_tp_web_home_button').click();
        await page.waitForTimeout(500);
        check('invalid unsaved form keeps native guard', page.url() === formUrl && await page.locator('.o_form_view').count() === 1 && !await page.locator('.o_tp_web_home').count());
        await shot(page, 'unsaved-native-guard');
        await context.close();

        const same = await login(browser, 'admin');
        const p = await same.newPage();
        await home(p);
        await p.locator('button.o_user_menu').click();
        await p.locator('[data-menu=logout]').click();
        await p.waitForURL(/\/web\/login/);
        const auth = await same.request.post(`${base}/web/session/authenticate`, { data: { jsonrpc: '2.0', method: 'call', params: { db, ...actors.employee } } });
        check('second user login same browser', Boolean((await auth.json()).result?.uid));
        await p.addInitScript(() => {
            window.__homeSeen = [];
            new MutationObserver(() => {
                window.__homeSeen.push(...[...document.querySelectorAll('.o_tp_web_home_tile')].map(el => el.dataset.menuXmlid));
            }).observe(document, { childList: true, subtree: true });
        });
        await home(p);
        const seen = await p.evaluate(() => window.__homeSeen);
        check('same-browser session never flashes admin/KH-KD menu', seen.length > 0 && !seen.includes('base.menu_administration') && !seen.includes(ids.kd));
        await same.close();
        const personal = await login(browser, 'actionuser');
        const own = await personal.newPage();
        await own.goto(`${base}/odoo`);
        await own.locator('.o-mail-Discuss').waitFor({ timeout: 30000 });
        check('own Home Action stays Discuss', !await own.locator('.o_tp_web_home').count());
        await personal.close();
        const multi = await login(browser, 'manager');
        const m = await multi.newPage();
        await home(m);
        await m.locator('button.o_switch_company_menu').click();
        await m.locator('.o_switch_company_item .log_into').filter({ hasText: 'UI HOME002' }).click();
        await m.waitForTimeout(500);
        await m.locator('.o_tp_web_home_tile').first().waitFor();
        check('company switch reloads permitted menu', !await m.locator(tile(ids.kd)).count());
        await multi.close();

        const mock = await login(browser, 'admin', { viewport: { width: 360, height: 844 } });
        const unknown = await mock.newPage();
        const longName = 'Hồ sơ khảo sát và kiểm tra công trình có tên ứng dụng rất dài';
        await unknown.route('**/web/webclient/load_menus', async route => {
            const response = await route.fetch();
            const menu = await response.json();
            const contact = Object.values(menu).find(x => x.xmlid === 'contacts.menu_contacts');
            Object.assign(contact, { xmlid: 'home002.unknown_app', name: longName,
                webIconData: 'data:image/png;base64,broken' });
            await route.fulfill({ response, json: menu });
        });
        await home(unknown);
        const unknownTile = unknown.locator(tile('home002.unknown_app'));
        await unknownTile.locator('.o_tp_web_home_icon_monogram').waitFor();
        check('unknown long app retains native name/destination', (await unknownTile.innerText()).includes(longName) && await unknownTile.getAttribute('href') === '/odoo/contacts');
        check('broken icon falls back once', await unknownTile.locator('img').count() === 0);
        check('long app label has no horizontal overflow', await unknownTile.evaluate(el => el.scrollWidth <= el.clientWidth + 1));
        await unknownTile.scrollIntoViewIfNeeded();
        await shot(unknown, 'unknown-long-name-fallback-360');
        await mock.close();
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
            const geometry = await p.evaluate(() => ({ dpr: devicePixelRatio, width: innerWidth, page: document.documentElement.scrollWidth <= innerWidth,
                home: document.querySelector('.o_tp_web_home').scrollWidth <= document.querySelector('.o_tp_web_home').clientWidth + 1 }));
            check(`real zoom ${zoom}`, Math.abs(geometry.dpr - zoom) < .01 && geometry.page && geometry.home, geometry);
            await shot(p, `admin-zoom-${zoom * 100}`);
        }
        await settings.locator('#zoomLevel').selectOption('1');
    } finally { await zoomContext.close(); }
};
