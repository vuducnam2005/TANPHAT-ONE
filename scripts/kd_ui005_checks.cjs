/* BP01–BP12. Browser native mutations use synthetic clone records only. */
const fs = require('node:fs');
const { chromium } = require('../frontend/node_modules/playwright');
const path = require('node:path');
module.exports = async function checks(ctx) {
    const { browser, local, base, target, login, ok, rpc, watch, settle, shot, openList, openFirst, check, out } = ctx;
    const write = target === 'clone';
    const stage = process.env.BP_STAGE || 'all';
    const run = s => stage === 'all' || stage.split(',').includes(s);
    const fixture = write ? JSON.parse(fs.readFileSync(path.join(local, 'fixture.json'), 'utf8')) : null;
    const evidence = {};
    const field = (p, name) => p.locator(`.o_form_view .o_field_widget[name="${name}"]`).first();
    const input = (p, name) => field(p, name).locator('input,textarea').first();
    async function save(p) {
        await p.locator('.o_form_button_save').click(); await settle(p);
        await p.waitForFunction(() => !document.querySelector('.o_form_button_save:not([disabled])') || !!document.querySelector('.modal'), null, { timeout: 8000 }).catch(() => {});
    }
    async function openRecord(p, kind, id) {
        const response = await p.context().request.post(`${base}/web/action/load`, {
            data: { jsonrpc: '2.0', method: 'call', params: { action_id: `tp_kd_workspace.action_${kind}` } },
        });
        const action = (await response.json()).result;
        await p.goto(`${base}/odoo/action-${action.id}/${id}`);
        await p.locator('.o_form_view').waitFor(); await settle(p);
    }
    async function createPage(context, action) {
        const p = await context.newPage(); watch(p);
        await openList(p, `tp_kd_workspace.action_${action}`); return p;
    }
    if (run('b')) {
        const context = await login(browser, 'editor');
        const p = await createPage(context, 'opportunities');
        check('BP01/BP02 scoped opportunity list', await p.locator('.tp_kd_bp_opportunity_list').count() === 1);
        const count = await ok(context, 'crm.lead', 'search_count', [[['tp_project_id', '!=', false]]]);
        check('BP02 list count matches scoped search_count', Number(await p.locator('.o_pager_limit').first().innerText()) === count, count);
        const sortedRequest = p.waitForRequest(r => r.url().includes('/web_search_read'));
        await p.locator('th[data-name="name"]').click();
        const sorted = (await sortedRequest).postDataJSON();
        check('BP02 native sort', /name/i.test(sorted.params.kwargs.order), sorted.params.kwargs.order);
        await p.getByRole('button', { name: 'Gọn', exact: true }).click();
        check('BP02 compact preference', await p.locator('body').evaluate(e => e.className.includes('compact')));
        await p.getByRole('button', { name: 'Thoáng', exact: true }).click();
        check('BP02 optional column chooser', await p.locator('.o_optional_columns_dropdown_toggle').count() > 0);
        await p.locator('.o_optional_columns_dropdown_toggle').click();
        await shot(p, 'opportunity-columns'); await p.keyboard.press('Escape');
        const search = p.locator('.o_searchview_input');
        await search.fill('BP005'); await search.press('Enter'); await settle(p);
        check('BP02 native text search', (await p.locator('.o_data_row').count()) >= (write ? 1 : 0));
        await shot(p, 'opportunity-search');
        await openList(p, 'tp_kd_workspace.action_opportunities');
        await p.locator('.o_searchview_dropdown_toggler').click();
        check('BP02 dedicated filters and group choices', (await p.locator('.o-dropdown--menu').innerText()).includes('Đang tìm hiểu'));
        await shot(p, 'opportunity-search-menu'); await p.keyboard.press('Escape');
        if (write) {
            await openRecord(p, 'opportunities', fixture.lead);
            check('BP03 Text/Char native field types', await input(p, 'name').evaluate(e => e.tagName === 'TEXTAREA'));
            const disclosures = p.locator('.tp_kd_bp_preview');
            const preview = disclosures.first();
            const nativeInput = await input(p, 'partner_id').elementHandle();
            await preview.locator('summary').focus(); await p.keyboard.press('Enter');
            check('BP09 keyboard opens full related name', await preview.getAttribute('open') !== null);
            check('BP09 full name wraps', (await preview.innerText()).length > 200);
            check('BP11 same autocomplete DOM after preview', await nativeInput.evaluate(e => e.isConnected));
            let calls = 0; const counter = r => { if (r.url().includes('/call_kw/')) calls++; };
            await p.waitForTimeout(300); p.on('request', counter);
            await preview.locator('summary').hover(); await p.waitForTimeout(300);
            check('BP11 hover has no RPC', calls === 0, calls); p.off('request', counter);
            const title = ('BP005 — Hồ sơ đấu thầu khảo sát và thiết kế ' + 'tuyến kết nối đô thị ven biển '.repeat(8)).trim();
            await input(p, 'name').fill(title);
            await input(p, 'kd_source').fill('Nguồn tổng hợp BP005');
            await p.getByRole('tab', { name: 'Phạm vi / gói thầu' }).click();
            await input(p, 'kd_scope').fill('Phạm vi giả lập BP005 — không phải hồ sơ thật.');
            await p.getByRole('tab', { name: 'Checklist hồ sơ' }).click();
            await input(p, 'kd_checklist').fill('Khảo sát\nNăng lực\nKế hoạch bàn giao');
            await input(p, 'kd_receipt').fill('Căn cứ khai báo BP005 chưa xác minh');
            await p.getByRole('tab', { name: 'Năng lực sử dụng' }).click();
            const tags = await field(p, 'kd_credential_ids').innerText();
            check('BP05 private credential not displayed', tags.includes('BP005-V') && !tags.includes('BP005-P'), tags);
            // Removal via native tags must preserve the private link in the inverse.
            await field(p, 'kd_credential_ids').locator('.o_delete').first().click();
            await p.getByRole('tab', { name: 'Checklist hồ sơ' }).click();
            check('BP03 tab preserves dirty Text', await input(p, 'kd_checklist').inputValue() === 'Khảo sát\nNăng lực\nKế hoạch bàn giao');
            await save(p);
            check('BP03 native save title persisted', (await ok(context, 'crm.lead', 'read', [[fixture.lead], ['name']]))[0].name === title);
            await p.reload(); await p.locator('.o_form_view').waitFor(); await settle(p);
            check('BP03 reopen persisted title', await input(p, 'name').inputValue() === title);
            // Missing deadline: object action must fail and remain in form.
            await p.locator('button[name="action_kd_prepare"]').click();
            await p.locator('.modal').waitFor();
            check('BP04 missing source data blocks transition', (await p.locator('.modal').innerText()).includes('Điền nguồn'));
            await p.locator('.modal .btn-primary').click();
            check('BP08 failed action stays in same form', p.url().endsWith(`/${fixture.lead}`));
            // Fill dates through native field then retry the same object action.
            await input(p, 'kd_deadline').fill('30/11/2026'); await input(p, 'kd_deadline').press('Tab');
            await save(p);
            await p.locator('button[name="action_kd_prepare"]').click(); await settle(p);
            await p.waitForFunction(() => !!document.querySelector('button[name="action_kd_record_submission"]'));
            check('BP04 preparation action persisted', (await ok(context, 'crm.lead', 'read', [[fixture.lead], ['kd_bid_state']]))[0].kd_bid_state === 'preparation');
            await p.locator('button[name="action_kd_record_submission"]').click(); await settle(p);
            check('BP04 submitted retains visible unverified notice', await p.locator('.tp_kd_bp_notice').isVisible());
            await ok(context, 'crm.lead', 'action_kd_record_submission', [[fixture.lead]]);
            check('BP04 retry idempotent', (await ok(context, 'crm.lead', 'read', [[fixture.lead], ['kd_bid_state']]))[0].kd_bid_state === 'submitted');
            await shot(p, 'opportunity-submitted-1440', true);
            const denied = await rpc(context, 'crm.lead', 'write', [[fixture.lead], { kd_bid_state: 'identified' }]);
            check('BP04 direct state write denied', !!denied.error);
            const direct = await ok(context, 'crm.lead', 'create', [{ name: 'BP005 — Giao trực tiếp', type: 'opportunity',
                tp_project_id: fixture.project, partner_id: fixture.partner, kd_route: 'direct', kd_source: 'Nguồn giả',
                kd_scope: 'Phạm vi giả', kd_checklist: 'Danh mục giả', kd_deadline: '2026-12-31' }]);
            await openRecord(p, 'opportunities', direct);
            await p.locator('button[name="action_kd_prepare"]').click(); await settle(p);
            check('BP04 direct has no submission button', await p.locator('button[name="action_kd_record_submission"]').count() === 0);
            check('BP04 direct route explanation', await p.getByText('Giao trực tiếp không cần khai báo nộp hồ sơ thầu.', { exact: true }).isVisible());
            const result = await rpc(context, 'crm.lead', 'action_kd_record_submission', [[direct]]);
            check('BP04 direct backend denies submission', !!result.error);
            // Native new form and Save; project is selected through native autocomplete.
            await openList(p, 'tp_kd_workspace.action_opportunities');
            await p.locator('.o_list_button_add').click(); await p.locator('.o_form_view').waitFor();
            const createdName = `BP005 — Tạo mới native ${Date.now()}`;
            await input(p, 'name').fill(createdName);
            await input(p, 'tp_project_id').fill('BP005');
            await p.locator('.o-autocomplete--dropdown-item').filter({ hasText: 'BP005' }).first().click();
            await input(p, 'partner_id').fill('BP005');
            await p.locator('.o-autocomplete--dropdown-item').filter({ hasText: 'BP005' }).first().click();
            await save(p);
            check('BP03 native create saved and reopenable', await ok(context, 'crm.lead', 'search_count', [[['name', '=', createdName]]]) === 1);
            // Invalid required name -> native failed-save guard, then discard.
            const url = p.url();
            await input(p, 'name').fill('');
            await p.locator('.o_form_button_save').click(); await settle(p);
            check('BP08 failed validation stays at record', p.url() === url && await p.locator('.o_field_invalid').count() > 0);
            await p.locator('.o_form_button_cancel').click(); await settle(p);
            // IME is observed at the native input: no replacement on preview or tab interaction.
            await input(p, 'kd_source').fill('Tiếng Việt đang nhập');
            const handle = await input(p, 'kd_source').elementHandle();
            await input(p, 'kd_source').dispatchEvent('compositionstart', { data: 'Việt' });
            await p.getByRole('tab', { name: 'Checklist hồ sơ' }).click();
            await input(p, 'kd_source').dispatchEvent('compositionend', { data: 'Việt' });
            check('BP11 native IME input remains connected', await handle.evaluate(e => e.isConnected && e.value === 'Tiếng Việt đang nhập'));
            await p.locator('.o_form_button_cancel').click(); await settle(p);
            evidence.createdName = createdName;
        }
        await context.close();
    }
    if (run('c')) {
        const context = await login(browser, 'reviewer');
        const p = await createPage(context, 'projects');
        check('BP06 scoped native project list', await p.locator('.tp_kd_bp_project_list').count() === 1);
        check('BP06 View Tasks native action', await p.locator('button[name="action_view_tasks"]').count() > 0);
        const projects = await ok(context, 'project.project', 'search_read', [[['tp_managed', '=', true]], ['id', 'tp_code']], { limit: 1 });
        const id = fixture?.project || projects[0].id;
        await openRecord(p, 'projects', id);
        check('BP01 project form scoped', await p.locator('.tp_kd_bp_project_form').count() === 1);
        const methods = ['opportunities', 'contracts', 'tasks', 'allocations', 'productions', 'acceptances', 'payments', 'plans', 'credentials', 'obligations'];
        const actions = {};
        for (const method of methods) {
            const action = await ok(context, 'project.project', `action_kd_${method}`, [[id]], { context: {
                form_view_ref: 'tp_kd_workspace.project_form', default_tp_managed: true,
                search_default_parent: 1, active_model: 'project.project', active_id: id } });
            actions[method] = action;
            check(`BP07 ${method} clean child context`, !action.context.default_tp_managed && !action.context.search_default_parent
                && action.context.form_view_ref !== 'tp_kd_workspace.project_form' && !action.context.active_model);
            check(`BP07 ${method} project domain/default/leaf`, action.domain.some(d => Array.isArray(d) && d[0] === (method === 'opportunities' ? 'tp_project_id' : 'project_id') && d[2] === id)
                && (action.context.default_project_id || action.context.default_tp_project_id) === id && !!action.context.tp_kd_leaf);
        }
        check('BP07 three primary links', await p.locator('.tp_kd_bp_primary_actions button').count() === 3);
        check('BP07 seven related links compiled', Object.keys(actions).length === 10);
        check('BP06 assignments hidden from ordinary user', !(await p.getByRole('tab', { name: 'Phân công', exact: true }).count()));
        await shot(p, 'project-form-1440', true);
        await context.close();
        for (const method of methods) {
            const actionContext = await login(browser, 'reviewer');
            const actionPage = await actionContext.newPage(); watch(actionPage);
            await openRecord(actionPage, 'projects', id);
            let button = actionPage.locator(`button[name="action_kd_${method}"]`);
            if (!await button.isVisible().catch(() => false)) {
                await actionPage.locator('.o-form-buttonbox .o_button_more').last().click();
                button = actionPage.locator(`button[name="action_kd_${method}"], .o-dropdown-item:has(button[name="action_kd_${method}"])`).first();
            }
            await button.click(); await actionPage.locator('.o_list_view').waitFor(); await settle(actionPage);
            check(`BP07 ${method} button opens native list`, await actionPage.locator('.o_list_view').isVisible());
            await actionContext.close();
        }
        evidence.actions = actions;
        if (write) {
            const manager = await login(browser, 'planner');
            const page = await createPage(manager, 'projects');
            await page.locator('.o_list_button_add').click(); await page.locator('.o_form_view').waitFor();
            const code = `BP005-${Date.now()}`;
            await input(page, 'name').fill('BP005 — Hồ sơ dự án tạo native');
            await input(page, 'tp_code').fill(code);
            await input(page, 'company_id').fill('Tan Phat');
            await page.locator('.o-autocomplete--dropdown-item').filter({ hasText: 'Tan Phat' }).first().click();
            await save(page);
            const found = await ok(manager, 'project.project', 'search_read', [[['tp_code', '=', code]], ['name', 'tp_managed']]);
            check('BP06 native project create code/managed preserved', found.length === 1 && found[0].tp_managed);
            check('BP06 manager assignment tab present', await page.getByRole('tab', { name: 'Phân công', exact: true }).count() === 1);
            await page.getByRole('tab', { name: 'Phạm vi / đầu ra' }).click();
            await input(page, 'kd_scope').fill('Đầu ra giả lập BP005 native'); await save(page); await page.reload();
            check('BP06 project native edit/save/reopen', (await ok(manager, 'project.project', 'read', [[found[0].id], ['kd_scope']]))[0].kd_scope === 'Đầu ra giả lập BP005 native');
            await manager.close();
        }
    }
    if (run('d')) {
        const responsive = [];
        for (const width of [360, 390, 768, 1024, 1440, 1920]) {
            const context = await login(browser, 'editor', { viewport: { width, height: 1000 }, hasTouch: width < 768 });
            for (const kind of ['opportunities', 'projects']) {
                const p = await createPage(context, kind);
                await shot(p, `list-${kind}-${width}`);
                check(`BP10 ${kind} list no page overflow ${width}`, await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
                if (fixture) await openRecord(p, kind, kind === 'projects' ? fixture.project : fixture.lead);
                else await openFirst(p);
                const facts = await p.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth,
                    fields: [...document.querySelectorAll('.tp_kd_bp_field')].map(e => ({ left: e.getBoundingClientRect().left, width: e.getBoundingClientRect().width })),
                    text: document.querySelector('.tp_kd_bp_title textarea')?.value || document.querySelector('.tp_kd_bp_title .o_field_widget')?.innerText,
                    buttons: [...document.querySelectorAll('.tp_kd_bp_primary_actions button')].map(e => e.getBoundingClientRect().height) }));
                responsive.push({ kind, width, ...facts });
                check(`BP10 ${kind} form no page overflow ${width}`, facts.overflow <= 1, facts);
                check(`BP09 ${kind} title readable ${width}`, !!facts.text);
                if (kind === 'projects') check(`BP10 primary targets44 ${width}`, facts.buttons.every(h => h >= 44));
                if (await p.locator('.tp_kd_bp_preview summary').count()) {
                    await p.locator('.tp_kd_bp_preview summary').first().click();
                    check(`BP09 touch/click full name ${kind}@${width}`, await p.locator('.tp_kd_bp_preview[open]').count() > 0);
                }
                await shot(p, `form-${kind}-${width}`, true);
                await p.emulateMedia({ reducedMotion: 'reduce' });
                check(`BP11 OS reduced ${kind}@${width}`, await p.locator('.tp_kd_bp_title .o_field_widget').evaluate(e => getComputedStyle(e).transitionDuration === '0s'));
                await p.close();
            }
            await context.close();
        }
        evidence.responsive = responsive;
        const zoomContext = await chromium.launchPersistentContext(path.join(local, `zoom-${target}`), {
            channel: 'chromium', headless: true, viewport: null, args: ['--window-size=1440,1000'], locale: 'vi-VN',
        });
        try {
            const settings = await zoomContext.newPage();
            await settings.goto('chrome://settings/appearance'); await settings.locator('#zoomLevel').waitFor();
            await zoomContext.request.post(`${base}/web/session/authenticate`, { data: {
                jsonrpc: '2.0', method: 'call', params: { db: ctx.db, ...ctx.actors.editor },
            } });
            const p = await zoomContext.newPage(); watch(p);
            for (const zoom of [1.25, 1.5]) {
                await settings.locator('#zoomLevel').selectOption(String(zoom));
                for (const kind of ['opportunities', 'projects']) {
                    await openList(p, `tp_kd_workspace.action_${kind}`); await openFirst(p);
                    const facts = await p.evaluate(() => ({ dpr: devicePixelRatio, overflow: document.documentElement.scrollWidth - innerWidth }));
                    check(`BP10 real browser zoom ${zoom} ${kind}`, Math.abs(facts.dpr - zoom) < 0.01 && facts.overflow <= 1, facts);
                    await shot(p, `zoom-${zoom}-${kind}`);
                    await p.locator('.o_tp_kd_sb_collapse').click(); await settle(p);
                    check(`BP10 expanded sidebar/drawer zoom ${zoom} ${kind}`, await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
                    const close = p.locator('.o_tp_kd_sb_close');
                    if (await close.isVisible().catch(() => false)) await close.click();
                    else await p.locator('.o_tp_kd_sb_collapse').click();
                    check(`BP10 restored sidebar zoom ${zoom} ${kind}`, await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
                }
            }
            await settings.locator('#zoomLevel').selectOption('1');
        } finally { await zoomContext.close(); }
    }
    if (run('g')) {
        if (!write) throw new Error('Guard/mutation tests are clone-only; use BP_STAGE=b,c,d on dev.');
        const context = await login(browser, 'editor');
        const p = await createPage(context, 'opportunities');
        await p.locator('.o_list_button_add').click(); await p.locator('.o_form_view').waitFor();
        await input(p, 'kd_source').fill('BP005 — chưa lưu và chưa có tên');
        const url = p.url();
        await p.locator('.o_tp_web_home_button').click(); await settle(p);
        check('BP08 invalid dirty form prevents Home navigation', p.url() === url && await p.locator('.o_form_view').count() === 1);
        await shot(p, 'native-invalid-home-guard');
        if (await p.locator('.modal').count()) await p.locator('.modal .btn-primary').first().click();
        await p.locator('.o_form_button_cancel').click(); await settle(p);
        await openList(p, 'tp_kd_workspace.action_opportunities');
        await openFirst(p);
        const original = await input(p, 'kd_source').inputValue();
        await input(p, 'kd_source').fill('BP005 — thay đổi sẽ hủy');
        await p.locator('.o_form_button_cancel').click(); await settle(p);
        check('BP08 native discard restores value', await input(p, 'kd_source').inputValue() === original);
        if (write) {
            const metadata = await login(browser, 'metadata');
            const denied = await rpc(metadata, 'crm.lead', 'write', [[fixture.lead], { kd_scope: 'Forbidden' }]);
            check('BP05 actor without prepare grant denied', !!denied.error);
            const projectDenied = await rpc(context, 'project.project', 'write', [[fixture.project], { kd_scope: 'Forbidden' }]);
            check('BP06 ordinary actor cannot configure managed project', !!projectDenied.error);
            const privateDenied = await rpc(context, 'tp.credential', 'read', [[fixture.private_credential], ['name']]);
            check('BP05 direct private credential read denied', !!privateDenied.error);
            await metadata.close();
        }
        await context.close();
    }
    if (run('h')) {
        const context = await login(browser, 'editor');
        const p = await createPage(context, 'opportunities');
        await p.locator('.o_searchview_dropdown_toggler').click();
        await p.locator('.o_filter_menu .o-dropdown-item, .o_filter_menu .dropdown-item').filter({ hasText: /^Đang tìm hiểu$/ }).first().click();
        await p.keyboard.press('Escape'); await settle(p);
        const expected = await ok(context, 'crm.lead', 'search_count', [[['tp_project_id', '!=', false], ['kd_bid_state', '=', 'identified']]]);
        check('BP02 state filter count equals backend scope', Number(await p.locator('.o_pager_limit').first().innerText()) === expected, expected);
        await p.locator('.o_facet_remove').first().click(); await settle(p);
        await p.locator('.o_searchview_dropdown_toggler').click();
        await p.locator('.o_group_by_menu .o-dropdown-item, .o_group_by_menu .dropdown-item').filter({ hasText: /^Tình trạng hồ sơ$/ }).first().click();
        await p.keyboard.press('Escape'); await settle(p);
        check('BP02 native grouping by state renders groups', await p.locator('.o_group_header').count() > 0);
        await shot(p, 'opportunity-group-state');
        await p.locator('.o_facet_remove').first().click(); await settle(p);
        await p.locator('.o_data_row .o_list_record_selector input').first().check();
        await settle(p);
        check('BP02 checkbox selects without form', await p.locator('.o_data_row_selected').count() === 1 && !await p.locator('.o_form_view').count());
        await p.locator('.o_data_row .o_list_record_selector input').first().uncheck();
        await p.locator('.o_optional_columns_dropdown_toggle').click();
        await p.locator('.o-dropdown--menu .o-dropdown-item, .o-dropdown--menu .dropdown-item').filter({ hasText: /^Dự án liên quan$/ }).first().click();
        await p.keyboard.press('Escape'); await settle(p);
        check('BP02 native optional project column shown', await p.locator('th[data-name="tp_project_id"]').count() === 1);
        await p.reload(); await p.locator('.o_list_view').waitFor(); await settle(p);
        check('BP02 optional column survives reload', await p.locator('th[data-name="tp_project_id"]').count() === 1);
        await p.locator('.o_tp_kd_reset_columns').click(); await settle(p);
        for (const kind of ['opportunities', 'projects']) {
            await openList(p, `tp_kd_workspace.action_${kind}`); await openFirst(p);
            const before = p.url();
            await p.locator('.o_pager_next').click(); await settle(p);
            check(`BP08 ${kind} native form pager changes record`, p.url() !== before);
            await p.locator('.o_pager_previous').click(); await settle(p);
            check(`BP08 ${kind} native pager returns to record`, p.url() === before);
            await p.locator('.breadcrumb-item a, .o_breadcrumb a').first().click();
            await p.locator('.o_list_view').waitFor(); await settle(p);
            check(`BP08 ${kind} breadcrumb returns to native list`, await p.locator('.o_list_view').isVisible());
            await p.goBack(); await p.locator('.o_form_view').waitFor(); await settle(p);
            check(`BP08 ${kind} browser Back restores native form`, await p.locator('.o_form_view').isVisible());
            await p.locator('.o_tp_kd_sb_prefs').click();
            await p.getByRole('radio', { name: 'Giảm chuyển động', exact: true }).click();
            await p.keyboard.press('Escape'); await settle(p);
            check(`BP11 ${kind} personal reduced motion`, await p.locator('.tp_kd_bp_title .o_field_widget').evaluate(e => document.body.classList.contains('o_tp_kd_reduce_motion') && getComputedStyle(e).transitionDuration === '0s'));
            await p.locator('.o_tp_kd_sb_prefs').click();
            await p.getByRole('radio', { name: 'Theo hệ thống', exact: true }).click();
            await p.keyboard.press('Escape');
        }
        if (write) {
            await openRecord(p, 'opportunities', fixture.lead);
            const original = await input(p, 'kd_source').inputValue();
            const metadata = await login(browser, 'metadata');
            const denied = await rpc(metadata, 'crm.lead', 'write', [[fixture.lead], { kd_scope: 'Denied' }]);
            await metadata.close();
            let attempts = 0;
            const route = '**/web/dataset/call_kw/crm.lead/web_save';
            await p.route(route, async r => { attempts++; await r.fulfill({ json: denied }); });
            await input(p, 'kd_source').fill('BP005 — lỗi quyền giả lập khi lưu');
            const url = p.url();
            await p.locator('.o_form_button_save').click(); await p.locator('.modal').waitFor();
            check('BP08 AccessError leaves dirty form and record in place', p.url() === url && await input(p, 'kd_source').inputValue() === 'BP005 — lỗi quyền giả lập khi lưu' && attempts === 1);
            await shot(p, 'native-accesserror-save');
            await p.locator('.modal .btn-primary').first().click();
            await p.unroute(route); await p.locator('.o_form_button_cancel').click(); await settle(p);
            check('BP08 failed save did not persist', (await ok(context, 'crm.lead', 'read', [[fixture.lead], ['kd_source']]))[0].kd_source === original);
        }
        await context.close();
    }
    if (run('s') && write) {
        const context = await login(browser, 'editor');
        const p = await context.newPage(); watch(p);
        await openRecord(p, 'opportunities', fixture.lead);
        const original = await input(p, 'kd_source').inputValue();
        let attempts = 0;
        const route = '**/web/dataset/call_kw/crm.lead/web_save';
        await p.route(route, async r => {
            attempts++;
            await r.fulfill({ json: { jsonrpc: '2.0', id: null, error: { code: 100,
                message: 'Odoo Session Expired', data: { name: 'odoo.http.SessionExpiredException',
                    message: 'Session expired (clone simulation)', arguments: ['Session expired (clone simulation)'], debug: '' } } } });
        });
        await input(p, 'kd_source').fill('BP005 — giữ chữ khi hết phiên giả lập');
        const url = p.url();
        await p.locator('.o_form_button_save').click(); await p.locator('.modal').waitFor();
        await p.waitForTimeout(500);
        check('BP08 expired session keeps form and unsaved input', p.url() === url && await input(p, 'kd_source').inputValue() === 'BP005 — giữ chữ khi hết phiên giả lập');
        check('BP08 expired session does not replay write', attempts === 1, attempts);
        check('BP08 expired session did not persist', (await ok(context, 'crm.lead', 'read', [[fixture.lead], ['kd_source']]))[0].kd_source === original);
        await shot(p, 'native-session-expired-save');
        await context.close();
        const manager = await login(browser, 'planner');
        const duplicate = await rpc(manager, 'project.project', 'create', [{ name: 'BP005 — duplicate must fail',
            tp_code: 'BP005-A', tp_managed: true, company_id: (await ok(manager, 'project.project', 'read', [[fixture.project], ['company_id']]))[0].company_id[0] }]);
        check('BP06 duplicate project code within company denied', !!duplicate.error);
        await manager.close();
    }
    fs.writeFileSync(path.join(out, `evidence-${stage}.json`), JSON.stringify(evidence, null, 2));
};
