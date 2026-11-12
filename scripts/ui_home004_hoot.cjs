const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const local = path.join(root, '.local/ui-home004');
const shots = path.join(local, 'shots/clone-hoot');
fs.mkdirSync(shots, { recursive: true });

const secret = JSON.parse(fs.readFileSync(path.join(root, '.local/dev-secrets.json')));

(async () => {
    const b = await chromium.launch({ headless: true });
    let ok = false;
    const summaries = [];
    try {
        const c = await b.newContext();
        const p = await c.newPage();
        console.log("Logging into clone on 19689...");
        await p.goto('http://127.0.0.1:19689/web/login?db=tp_tanphat_home004_20261110');
        await p.locator('[name=login]').fill('admin');
        await p.locator('[name=password]').fill(secret.admin);
        await p.locator('button[type=submit]').click();
        await p.locator('.o_web_client').waitFor({ timeout: 120000 });

        for (const module of ['tp_web_home']) {
            console.log(`Running HOOT tests for ${module}...`);
            const logs = [];
            const listener = (m) => logs.push(m.text());
            p.on('console', listener);
            await p.goto(`http://127.0.0.1:19689/web/tests?headless&debug=assets&filter=${module}`, { timeout: 180000 });
            const end = Date.now() + 240000;
            while (!logs.some((l) => /Test suite succeeded|Some tests failed/i.test(l)) && Date.now() < end) {
                await p.waitForTimeout(500);
            }
            const passed = logs.some((l) => /Test suite succeeded/i.test(l));
            const bodyText = await p.locator('body').innerText();
            fs.writeFileSync(path.join(shots, `hoot-${module}.txt`), bodyText + '\n' + logs.join('\n'));
            summaries.push({ module, passed });
            p.off('console', listener);
            if (!passed) {
                console.error("HOOT test output:", bodyText);
                console.error("Logs:", logs.slice(-20).join('\n'));
            }
            assert(passed, 'HOOT failed; check output');
        }
        ok = true;
    } finally {
        await b.close();
        const treeHashes = JSON.parse(fs.readFileSync(path.join(local, 'tested-source.json')));
        fs.writeFileSync(path.join(shots, 'result.json'), JSON.stringify({ ok, summaries, source_hashes: treeHashes }, null, 2));
        console.log(JSON.stringify({ ok, summaries }));
        process.exitCode = ok ? 0 : 1;
    }
})();
