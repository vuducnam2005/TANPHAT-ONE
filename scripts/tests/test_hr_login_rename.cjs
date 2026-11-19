// Synthetic HttpCase only: the caller supplies a private fixture with test cookies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

async function run() {
    const fixture = JSON.parse(fs.readFileSync(process.env.TP_LOGIN_RENAME_FIXTURE, 'utf8'));
    assert.equal(new URL(fixture.base).port, '18079');
    assert(fixture.employeeName.startsWith('Synthetic '));
    const output = path.resolve(fixture.output);
    fs.mkdirSync(output, { recursive: true });
    const browser = await chromium.launch({ headless: true });
    const errors = [], checks = [];
    let page;
    try {
        const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN' });
        await context.addCookies(fixture.cookies);
        page = await context.newPage();
        page.setDefaultTimeout(45000);
        page.on('pageerror', e => errors.push(e.message));
        await page.goto(`${fixture.base}/app/action-tp_hr_workspace.action_employees/${fixture.employeeId}`, { waitUntil: 'domcontentloaded' });
        await page.locator('.o_form_view').waitFor();
        await page.locator('[role="tab"][name="page_account"]').click();
        const button = page.getByRole('button', { name: 'Đổi tên đăng nhập', exact: true });
        await button.waitFor();
        await page.screenshot({ path: path.join(output, 'account-before.png') });
        await button.click();
        const dialog = page.getByRole('dialog').filter({ has: page.locator('#tp_login_new') });
        await dialog.waitFor();
        assert.equal(await dialog.locator('#tp_login_current').inputValue(), fixture.oldLogin);
        await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
        await dialog.getByRole('alert').waitFor();
        assert.match(await dialog.getByRole('alert').innerText(), /Vui lòng/);
        await dialog.locator('#tp_login_new').fill('bad name');
        await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
        assert.match(await dialog.getByRole('alert').innerText(), /khoảng trắng/);
        await dialog.locator('#tp_login_new').fill(fixture.takenLogin);
        await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
        await page.waitForFunction(() => document.querySelector('#tp_login_error')?.textContent.includes('đã tồn tại'));
        assert.equal(await dialog.locator('#tp_login_current').inputValue(), fixture.oldLogin);
        await page.screenshot({ path: path.join(output, 'duplicate-inline.png') });
        checks.push('Blank, whitespace and duplicate reported inline; old login kept');
        await dialog.getByRole('button', { name: 'Hủy', exact: true }).click();
        await dialog.waitFor({ state: 'hidden' });
        await button.click();
        await dialog.locator('#tp_login_new').fill(fixture.newLogin);
        await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
        await dialog.waitFor({ state: 'hidden' });
        await page.waitForFunction(name => [...document.querySelectorAll('[name="tp_user_login"]')].some(el => el.textContent.includes(name)), fixture.newLogin);
        await page.screenshot({ path: path.join(output, 'account-after.png') });
        checks.push('Save updates employee detail after native reload');
        if (fixture.grantedAdmin) {
            assert.equal(await page.getByRole('button', { name: 'Đặt lại mật khẩu', exact: true }).count(), 0);
            checks.push('Original admin sees rename for granted admin while lock/reset stay protected');
        }
        await button.click();
        assert.equal(await dialog.locator('#tp_login_current').inputValue(), fixture.newLogin);
        await dialog.getByRole('button', { name: 'Hủy', exact: true }).click();
        checks.push('Reopening dialog reads new login; Cancel does not write');
        await page.setViewportSize({ width: 390, height: 844 });
        await button.click();
        await dialog.locator('#tp_login_new').waitFor();
        const bounds = await dialog.boundingBox();
        assert(bounds.width <= 390 && bounds.x >= 0);
        await page.screenshot({ path: path.join(output, 'dialog-mobile.png') });
        await page.keyboard.press('Escape');
        await dialog.waitFor({ state: 'hidden' });
        checks.push('Mobile 390px dialog fits; Escape closes');
        assert.deepEqual(errors, []);
        fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify({ checks, errors }, null, 2));
        console.log(JSON.stringify({ checks: checks.length, errors }));
    } catch (error) {
        if (page) {
            await page.screenshot({ path: path.join(output, 'failure.png') });
            fs.writeFileSync(path.join(output, 'failure.html'), await page.content());
        }
        console.error(JSON.stringify({ errors, url: page?.url() }));
        throw error;
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exitCode = 1; });
