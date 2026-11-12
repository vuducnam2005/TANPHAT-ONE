const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),local=path.join(root,'.local/kd-access002');
const secret=JSON.parse(fs.readFileSync(path.join(root,'.local/dev-secrets.json')));
(async()=>{const b=await chromium.launch({headless:true});let ok=false;const summaries=[];try{const c=await b.newContext();const p=await c.newPage();
await p.goto('http://127.0.0.1:19289/web/login?db=tp_tanphat_kdaccess002_20261109');await p.locator('[name=login]').fill('admin');await p.locator('[name=password]').fill(secret.admin);await p.locator('button[type=submit]').click();await p.locator('.o_web_client').waitFor({timeout:120000});
for(const module of ['tp_kd_workspace','tp_web_home']){const logs=[];const listener=m=>logs.push(m.text());p.on('console',listener);
await p.goto(`http://127.0.0.1:19289/web/tests?headless&debug=assets&filter=${module}`,{timeout:180000});const end=Date.now()+240000;
while(!logs.some(l=>/Test suite succeeded|Some tests failed/i.test(l))&&Date.now()<end)await p.waitForTimeout(500);
const passed=logs.some(l=>/Test suite succeeded/i.test(l));fs.writeFileSync(path.join(local,`hoot-${module}.txt`),(await p.locator('body').innerText())+'\n'+logs.join('\n'));summaries.push({module,passed});p.off('console',listener);assert(passed,'HOOT failed; private evidence');}
ok=true;}finally{await b.close();fs.writeFileSync(path.join(local,'hoot-result.json'),JSON.stringify({ok,summaries},null,2));console.log(JSON.stringify({ok,summaries}));process.exitCode=ok?0:1;}})();
