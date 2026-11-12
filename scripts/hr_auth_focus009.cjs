// Real Chrome regression. Synthetic fixture/profile only; never use this writer on main.
// Fixture and saved Chrome credential are prepared privately under .local/hr-auth-focus009.
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const dir = '.local/hr-auth-focus009';
const f = JSON.parse(fs.readFileSync(`${dir}/fixture.json`, 'utf8'));
const base = 'http://127.0.0.1:18079';
const checks = [], errors = [];
const redact = text => [f.password, f.newPassword, f.resetPassword].reduce((s, v) => s.replaceAll(v, '[redacted]'), String(text));
(async () => {
    const context = await chromium.launchPersistentContext(`${dir}/chrome-profile`, {
        channel: 'chrome', headless: true, ignoreDefaultArgs: ['--enable-automation', '--disable-extensions'],
        viewport: { width: 1440, height: 1000 }, permissions: ['clipboard-read', 'clipboard-write'],
    });
    const page = context.pages()[0];
    page.on('pageerror', e => errors.push(redact(e.message)));
    page.on('console', m => { if (m.type() === 'error') errors.push(redact(m.text())); });
    const search = () => page.locator('.o_tp_hr_sb_search input');
    const identity = () => page.locator('.o_tp_identity_check');
    const pass = () => identity().locator('[name=password] input');
    const focused = selector => page.evaluate(s => document.activeElement?.matches(s), selector);
    const modalFocus = () => page.evaluate(() => !!document.activeElement?.closest('.modal:not(.o_inactive_modal)'));
    const settled = () => page.evaluate(() => new Promise(resolve => {
        let frames = 8; const next = () => --frames ? requestAnimationFrame(next) : resolve(); requestAnimationFrame(next);
    }));
    const rpc = async (model, method, args) => (await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {
        data: { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs: {} } },
    })).json();
    async function login() {
        await context.clearCookies();
        const r = await context.request.post(`${base}/web/session/authenticate`, { data: {
            jsonrpc: '2.0', method: 'call', params: { db: 'tp_tanphat_test', login: f.login, password: f.password },
        } });
        assert.equal((await r.json()).result?.uid, f.adminId);
        await page.goto(`${base}/odoo/action-tp_hr_workspace.action_employees/${f.employee}`);
        await page.locator('.o_tp_hr_position_entry').waitFor();
        await page.locator('.nav-link[name=page_account]').click();
    }
    async function open(reset) {
        await page.locator('[name=action_open_account_dialog]').click();
        if (reset) await page.locator('[name=action_reset_password]').click();
        await identity().waitFor(); await settled();
        assert(await modalFocus());
        assert(await focused('[name=password] input'));
    }
    async function confirm() {
        await pass().fill(''); await pass().focus(); await page.keyboard.type(f.password);
        await page.locator('[name=run_check]').click();
        await page.locator('#tp_account_login').waitFor(); await settled();
    }
    async function cancelCredentials() {
        await page.locator('.o_tp_hr_credentials').getByRole('button', { name: 'Hủy', exact: true }).click();
        await page.locator('#tp_account_login').waitFor({ state: 'hidden' });
    }
    let ok = false;
    try {
        const saved = execFileSync('.venv/Scripts/python.exe', ['-c',
            'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute("SELECT count(*) FROM logins WHERE origin_url=? AND username_value=? AND length(password_value)>0",sys.argv[2:]).fetchone()[0])',
            `${dir}/chrome-profile/Default/Login Data`, `${base}/`, f.login], { encoding: 'utf8' });
        assert(Number(saved.trim()) > 0, 'Seed a synthetic credential through Chrome password manager before running this regression.');
        await login();
        const previous = await rpc('hr.employee', 'read', [[f.employee], ['user_id']]);
        if (previous.result[0].user_id) {
            const row = await rpc('hr.employee', 'create', [[{ name: 'Nhân viên giả focus 009', department_id: f.department }]]);
            assert(!row.error); f.employee = row.result[0]; f.accountLogin = `focus009.employee.${f.employee}`;
            fs.writeFileSync(`${dir}/fixture.json`, JSON.stringify(f));
        }
        // Empty and deliberately entered filters: native password manager must not modify either.
        for (const query of ['', 'nhan vien']) {
            await login(); await search().fill(query); await search().press('Enter');
            assert.equal(await search().inputValue(), query);
            await open(false); assert.equal(await search().inputValue(), query);
            for (const key of ['Tab', 'Shift+Tab']) for (let i = 0; i < 12; i++) { await page.keyboard.press(key); assert(await modalFocus()); }
            await pass().focus(); await page.keyboard.type('wrong-focus009');
            await page.locator('[name=run_check]').click();
            await page.locator('.o_error_dialog').waitFor();
            assert.match(await page.locator('.o_error_dialog').innerText(), /Mật khẩu.*chưa đúng/);
            await page.keyboard.press('Escape'); await identity().waitFor(); await settled();
            assert(await modalFocus()); assert.equal(await search().inputValue(), query);
            await page.keyboard.press('Escape'); await identity().waitFor({ state: 'hidden' });
            assert(await focused('[name=action_open_account_dialog]'));
            assert.equal(await search().inputValue(), query);
            await open(false); await confirm();
            assert(await focused('#tp_account_login'));
            assert.equal(await search().inputValue(), query);
            await cancelCredentials();
            assert.equal(await search().inputValue(), query);
            checks.push(`Real saved Chrome credential: filter ${query ? 'existing' : 'empty'}, wrong/retry, Tab/Shift+Tab, Escape, reopen, correct identity, create focus/cancel preserved`);
        }
        await login(); await open(false); await confirm();
        await page.keyboard.type(f.accountLogin);
        await page.locator('#tp_account_password').focus(); await page.keyboard.type(f.newPassword);
        await page.locator('#tp_account_confirmation').focus(); await page.keyboard.type(f.newPassword);
        await page.keyboard.press('Enter'); await page.locator('#tp_account_login').waitFor({ state: 'hidden' });
        const created = await rpc('hr.employee', 'read', [[f.employee], ['user_id']]);
        assert(created.result[0].user_id); f.createdUser = created.result[0].user_id[0];
        const userContext = await context.browser().newContext();
        const auth = password => userContext.request.post(`${base}/web/session/authenticate`, { data: {
            jsonrpc: '2.0', method: 'call', params: { db: 'tp_tanphat_test', login: f.accountLogin, password },
        } }).then(r => r.json());
        assert.equal((await auth(f.newPassword)).result?.uid, f.createdUser);
        await userContext.close(); checks.push('Synthetic account created through keyboard Enter and logs in with chosen password');
        for (const mode of ['desktop', 'rail', 'mobile']) {
            await page.setViewportSize(mode === 'mobile' ? { width: 390, height: 844 } : { width: 1440, height: 1000 });
            await login();
            if (mode === 'mobile') { await page.locator('.o_tp_hr_menu_toggle').click(); await search().fill('nhan vien'); await page.getByRole('button', { name: 'Đóng menu', exact: true }).click(); }
            else await search().fill('nhan vien');
            if (mode === 'rail') await page.locator('.o_tp_hr_sb_collapse').click();
            await open(true);
            if (mode === 'desktop') {
                await pass().fill('');
                await page.evaluate(value => navigator.clipboard.writeText(value), f.password);
                await pass().focus(); await page.keyboard.press('Control+V');
                assert.equal(await pass().inputValue(), f.password);
                await page.locator('[name=run_check]').click(); await page.locator('#tp_account_password').waitFor(); await settled();
            } else await confirm();
            assert(await focused('#tp_account_password'));
            await page.locator('#tp_account_password').focus(); await page.keyboard.type(f.resetPassword);
            await page.locator('#tp_account_confirmation').focus(); await page.keyboard.type(f.resetPassword);
            if (mode === 'desktop') {
                fs.writeFileSync(`${dir}/session.json`, JSON.stringify({ sid: (await context.cookies()).find(c => c.name === 'session_id').value }));
                execFileSync('.venv/Scripts/python.exe', ['-X', 'utf8', 'odoo-bin', 'shell', '-c', '.local/test/odoo.conf', '-d', 'tp_tanphat_test', '--no-http', '--logfile', `${dir}/expire.log`], { input: fs.readFileSync(`${dir}/expire.py`), stdio: ['pipe', 'pipe', 'pipe'] });
                await page.getByRole('button', { name: 'Lưu mật khẩu mới', exact: true }).click();
                await page.locator('.o_tp_hr_credential_error').waitFor();
                assert.match(await page.locator('.o_tp_hr_credential_error').innerText(), /hết hạn/);
                await cancelCredentials(); await page.keyboard.press('Escape');
                checks.push('Real clipboard paste goes to identity password; expired identity blocks password write');
            } else if (mode === 'rail') {
                await page.getByRole('button', { name: 'Lưu mật khẩu mới', exact: true }).click();
                await page.locator('#tp_account_login').waitFor({ state: 'hidden' });
            } else await cancelCredentials();
            await page.keyboard.press('Escape');
            if (mode === 'rail') await page.locator('.o_tp_hr_sb_collapse').click();
            if (mode === 'mobile') await page.locator('.o_tp_hr_menu_toggle').click();
            assert.equal(await search().inputValue(), 'nhan vien');
            await search().fill('nhan vien'); assert.equal(await search().inputValue(), 'nhan vien');
            await search().press('Escape'); await settled(); assert.equal(await search().inputValue(), '');
            await page.screenshot({ path: `${dir}/after-${mode}.png`, mask: [page.locator('input[type=password]')] });
            checks.push(`${mode}: reset dialog focus, keyboard flow, cancel/save and sidebar search usable afterwards`);
        }
        const verifyContext = await context.browser().newContext();
        const result = await verifyContext.request.post(`${base}/web/session/authenticate`, { data: { jsonrpc: '2.0', method: 'call', params: { db: 'tp_tanphat_test', login: f.accountLogin, password: f.resetPassword } } });
        assert.equal((await result.json()).result?.uid, f.createdUser); await verifyContext.close();
        checks.push('Reset password successfully authenticates synthetic employee');
        assert.deepEqual(errors, []); ok = true;
    } catch (e) {
        errors.push(redact(e.stack));
    } finally {
        fs.writeFileSync(`${dir}/browser-result.json`, JSON.stringify({ ok, checks, errors, chrome: context.browser().version() }, null, 2));
        console.log(JSON.stringify({ ok, checks, errors }));
        await context.close(); process.exitCode = ok ? 0 : 1;
    }
})();
