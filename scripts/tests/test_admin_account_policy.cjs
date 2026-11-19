// Invoked only by the synthetic HttpCase; private cookies are deleted by its caller.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

async function run() {
    const f = JSON.parse(fs.readFileSync(process.env.TP_ADMIN_POLICY_FIXTURE, 'utf8'));
    assert.equal(new URL(f.base).port, '18079');
    assert(f.employeeName.startsWith('Synthetic '));
    const browser = await chromium.launch({ headless: true });
    const errors = [], checks = [];
    let page;
    try {
        const context = await browser.newContext({ locale: 'vi-VN' });
        await context.addCookies(f.cookies);
        page = await context.newPage();
        page.setDefaultTimeout(45000);
        page.on('pageerror', e => errors.push(e.message));
        async function open(id) {
            await page.goto(`${f.base}/app/action-tp_hr_workspace.action_employees/${id}`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_form_view').waitFor();
            await page.locator('[role="tab"][name="page_account"]').click();
        }
        for (const [size, width, height] of [['desktop', 1440, 900], ['mobile', 390, 844]]) {
            await page.setViewportSize({ width, height });
            await open(f.employeeId);
            if (f.mode === 'original') {
                await page.getByRole('button', { name: 'Khóa / mở tài khoản', exact: true }).click();
                let dialog = page.getByRole('dialog').filter({ has: page.locator('[name="reason"]') });
                await dialog.waitFor();
                assert.match(await dialog.locator('[name="account_kind"]').innerText(), /Admin ủy quyền/);
                await page.screenshot({ path: path.join(f.output, `${f.mode}-${size}-before.png`) });
                await dialog.locator('[name="reason"] input').fill('Synthetic browser lock audit');
                await dialog.locator('button[name="action_lock"]').click();
                const confirm = page.getByRole('dialog').filter({ hasText: 'Khóa đăng nhập và kết thúc' });
                await confirm.waitFor();
                await confirm.getByRole('button', { name: 'Khóa tài khoản', exact: true }).click();
                await dialog.waitFor({ state: 'hidden' });
                await page.getByRole('button', { name: 'Khóa / mở tài khoản', exact: true }).click();
                dialog = page.getByRole('dialog').filter({ has: page.locator('[name="reason"]') });
                await dialog.locator('button[name="action_unlock"]').waitFor();
                assert.equal(await dialog.locator('button[name="action_lock"]').count(), 0);
                await page.screenshot({ path: path.join(f.output, `${f.mode}-${size}-locked.png`) });
                await dialog.locator('[name="reason"] input').fill('Synthetic browser unlock audit');
                await dialog.locator('button[name="action_unlock"]').click();
                await dialog.waitFor({ state: 'hidden' });
                await open(f.employeeId);
                await page.screenshot({ path: path.join(f.output, `${f.mode}-${size}-unlocked.png`) });
                for (const [id, label] of [[f.originalEmployeeId, 'Admin gốc'], [f.normalEmployeeId, 'Nhân viên']]) {
                    await open(id);
                    assert.match(await page.locator('[name="tp_admin_level"]').innerText(), new RegExp(label));
                }
                checks.push(`${size}: original locks/unlocks granted admin; account types rendered`);
            } else {
                await page.getByText('Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.', { exact: true }).first().waitFor();
                for (const name of ['Đổi tên đăng nhập', 'Đặt lại mật khẩu', 'Khóa / mở tài khoản', 'Sửa hồ sơ']) {
                    assert.equal(await page.getByRole('button', { name, exact: true }).count(), 0);
                }
                assert.equal(await page.locator('.o_form_view [name="name"] input').count(), 0);
                await page.screenshot({ path: path.join(f.output, `${f.mode}-${size}-readonly.png`) });
                checks.push(`${size}: peer profile readonly with reason and no account mutation controls`);
                await page.goto(`${f.base}/app/action-base.action_res_users/${f.targetUserId}`, { waitUntil: 'domcontentloaded' });
                await page.locator('.o_form_view').waitFor();
                await page.getByText('Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.', { exact: true }).first().waitFor();
                assert.equal(await page.locator('.o_form_view [name="name"] input').count(), 0);
                assert.equal(await page.locator('.o_form_view [name="login"] input').count(), 0);
                assert.equal(await page.locator('.o_form_button_edit:visible, .o_form_button_save:visible, .o_cp_action_menus:visible').count(), 0);
                await page.screenshot({ path: path.join(f.output, `${f.mode}-${size}-user-readonly.png`) });
                checks.push(`${size}: native peer user form readonly with no edit/save/action menu`);
            }
        }
        assert.deepEqual(errors, []);
        fs.writeFileSync(path.join(f.output, `${f.mode}-result.json`), JSON.stringify({ checks, errors }, null, 2));
        console.log(JSON.stringify({ checks, errors }));
    } catch (error) {
        if (page) {
            await page.screenshot({ path: path.join(f.output, `${f.mode}-failure.png`) });
            fs.writeFileSync(path.join(f.output, `${f.mode}-failure.html`), await page.content());
            console.error(JSON.stringify({ errors, url: page.url(),
                dialogs: await page.getByRole('dialog').allTextContents(),
                technical: await page.locator('.o_error_detail, .o_error_dialog, .o_error_dialog_content').allTextContents() }));
        }
        throw error;
    } finally { await browser.close(); }
}
run().catch(error => { console.error(error); process.exitCode = 1; });
