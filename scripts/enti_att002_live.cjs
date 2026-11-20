// ENTI-ATTENDANCE-002: "new punch appears without F5" on the LOCAL test server only (18179 / tp_tanphat_test).
// Opens Tổng quan, then runs scripts/enti_att002_live_punch.py through `odoo-bin shell` (fake ENTI answer through
// the real apply path, local test DB only) and waits for the screen to show the new out time without a reload.
// It measures ENTI→Odoo→screen only; the machine→ENTI leg is outside Odoo and is not measured here.
const {chromium} = require('../frontend/node_modules/playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const base = process.env.TP_BASE || 'http://127.0.0.1:18179';
const login = JSON.parse(fs.readFileSync(path.join(root, '.local/test/ui_login.json'), 'utf8'));
assert.equal(login.db, 'tp_tanphat_test');

(async () => {
    const browser = await chromium.launch({headless: true});
    const page = await browser.newPage({viewport: {width: 1440, height: 900}});
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    try {
        await page.goto(`${base}/web/login?db=${login.db}`);
        await page.locator('[name=login]').fill(login.login);
        await page.locator('[name=password]').fill(login.password);
        await page.locator('button[type=submit]').click();
        await page.locator('.o_web_client').waitFor({timeout: 120000});
        await page.goto(`${base}/odoo/cham-cong`);
        await page.locator('.o_tp_att_ov_recent_table tbody tr').first().waitFor({timeout: 90000});
        await page.evaluate(() => { window.__tpNoReload = true; });
        const outBefore = Number(await page.locator('.o_tp_att_ov_group.o_done strong').innerText());
        await page.waitForTimeout(1500); // let the bus subscription settle

        const shell = spawnSync(path.join(root, '.venv/Scripts/python.exe'), [
            '-X', 'utf8', 'odoo-bin', 'shell', '-c', '.local/test/odoo.conf', '-d', 'tp_tanphat_test', '--no-http', '--log-level=warn',
        ], {cwd: root, input: fs.readFileSync(path.join(__dirname, 'enti_att002_live_punch.py')), encoding: 'utf8', timeout: 180000});
        const line = (shell.stdout || '').trim().split('\n').filter((l) => l.startsWith('{')).pop();
        assert.ok(line, 'shell probe failed: ' + (shell.stderr || '').slice(-800));
        const punch = JSON.parse(line);
        assert.equal(punch.applied, 1);

        await page.waitForFunction(({employee, out}) => {
            const li = document.querySelector('.o_tp_att_ov_recent_table tbody tr');
            return li && li.innerText.includes(employee) && li.innerText.includes(out);
        }, punch, {timeout: 90000, polling: 200});
        const seconds = (Date.now() / 1000 - punch.committed_at).toFixed(1);
        assert.ok(await page.evaluate(() => window.__tpNoReload === true), 'the page must not reload');
        const outAfter = Number(await page.locator('.o_tp_att_ov_group.o_done strong').innerText());
        assert.equal(outAfter, outBefore + 1, 'card "Đã về" follows the new punch');
        assert.deepEqual(errors, []);
        console.log(`PASS live update without reload: ${punch.employee} Ra ${punch.out} shown ${seconds}s after commit; `
            + `Đã về ${outBefore} → ${outAfter}`);
    } catch (error) {
        console.error('FAIL', error.message, errors);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
