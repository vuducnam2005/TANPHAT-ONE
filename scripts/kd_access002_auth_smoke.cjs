/* Read-only auth regression on dev; credentials remain private. */
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.local/kd-access002'),base='http://127.0.0.1:18069';
(async()=>{const b=await chromium.launch({headless:true});let ok=false;const checks=[],errors=[];try{
 const c=await b.newContext({viewport:{width:1440,height:1000}}),p=await c.newPage();
 const creds=JSON.parse(fs.readFileSync(path.join(root,'.local/kd-access001/dev-credentials.json'))).support;
 p.on('pageerror',e=>errors.push(e.message));
 await p.goto(base+'/web/login?db=tp_tanphat_dev');await p.locator('.tp-native-login').waitFor();
 await p.screenshot({path:path.join(out,'shots/dev/after/native-login.png')});
 await p.locator('[name=login]').fill(creds.login);await p.locator('[name=password]').fill(creds.password);await p.locator('button[type=submit]').click();
 await p.locator('.o_tp_web_home').waitFor({timeout:120000});checks.push('native branded login and Home');
 await p.locator('.o_user_menu').click();await p.locator('[data-menu=preferences]').waitFor();checks.push('native preferences retained');
 const response=p.waitForResponse(r=>r.url().includes('/web/session/logout')&&r.request().method()==='POST');
 await p.locator('[data-menu=logout]').click();await response;await p.locator('.tp-native-login').waitFor({timeout:60000});checks.push('native POST logout returned branded login/chooser');
 assert((await c.request.get(base+'/api/v1/me')).status()===401);checks.push('protected API rejects ended session');
 await p.screenshot({path:path.join(out,'shots/dev/after/native-logout.png')});assert(errors.length===0);ok=true;
}catch(e){errors.push(e.message);}finally{await b.close();fs.writeFileSync(path.join(out,'dev-auth-smoke.json'),JSON.stringify({ok,checks,passed:checks.length,errors},null,2));console.log(JSON.stringify({ok,passed:checks.length,errors:errors.length}));process.exitCode=ok?0:1;}})();
