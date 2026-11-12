/* Native account shortcut: clone may save/restore phone; dev opens/cancels only. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..'), local = path.join(root, '.local/kd-account001');
const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const owner = read('.local/kd-account001/owner.json');
assert(owner.rehearsal_passed && owner.database === 'tp_tanphat_kdaccount001_20261108' && owner.http_port === 19089);
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : 19089}`;
const actors = read('.local/kd-access001/dev-credentials.json');
actors.admin = {login:'admin',password:read('.local/dev-secrets.json').admin};
const redact = value => Object.values(actors).reduce(
    (text,actor)=>text.replaceAll(actor.password,'[REDACTED]'),String(value));
const out = path.join(local, 'shots', target); fs.mkdirSync(out, {recursive:true});
const checks=[], failures=[], errors=[];
const check = (name, value) => {assert(value, name); checks.push(name);};
function sourceHashes() {
    const dir=path.join(root,target==='clone'?'.local/kd-account001/source/custom_addons/tp_kd_workspace':'custom_addons/tp_kd_workspace');
    const hashes={};
    function walk(folder) {
        for(const entry of fs.readdirSync(folder,{withFileTypes:true})) {
            if(entry.name==='__pycache__'||entry.name.endsWith('.pyc'))continue;
            const file=path.join(folder,entry.name);
            if(entry.isDirectory())walk(file);
            else hashes[path.relative(dir,file).split(path.sep).join('/')]=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
        }
    }
    walk(dir); return hashes;
}
const initialHashes=sourceHashes();
async function rpc(c,model,method,args=[],kwargs={}) {
    const r=await (await c.request.post(`${base}/web/dataset/call_kw/${model}/${method}`,{
        data:{jsonrpc:'2.0',method:'call',params:{model,method,args,kwargs}},
    })).json();
    assert(!r.error,r.error?.data?.message);return r.result;
}
async function shot(p,name) {await p.screenshot({path:path.join(out,`${name}.png`),animations:'disabled'});}
async function open(p, keyboard=false) {
    const button=p.getByRole('button',{name:'Tài khoản',exact:true});
    if(keyboard){await button.focus();await p.keyboard.press('Enter');}else await button.click();
    await p.locator('.o_dialog .o_form_view').waitFor({timeout:30000});
}
async function cancel(p) {
    await p.locator('.o_dialog button[name="preference_cancel"]').click();
    await p.locator('.o_dialog').waitFor({state:'hidden'});
}
async function saveProfile(p) {
    assert(target==='clone','Dev profile save is forbidden.');
    await Promise.all([
        p.waitForEvent('framenavigated',{predicate:frame=>frame===p.mainFrame(),timeout:60000}),
        p.locator('.o_dialog button[name="preference_save"]').click(),
    ]);
    await p.locator('.o_tp_kd_ov').waitFor({timeout:60000});
}
async function overview(p) {
    await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`,{timeout:120000});
    await p.locator('.o_tp_kd_ov').waitFor({timeout:60000});
}
(async()=>{
 const browser=await chromium.launch({headless:true});let current;
 try {
  for(const [alias,credential] of Object.entries(actors)) {
   const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'vi-VN'});
   try {
    const p=await context.newPage();current=p;
    p.on('pageerror',e=>errors.push(redact(alias+': '+e.message)));
    p.on('console',m=>{if(m.type()==='error')errors.push(redact(alias+': '+m.text()));});
    const profileReads=[];
    p.on('request',r=>{
        if(r.url().includes('/res.users/web_read')) {
            const data=r.postDataJSON();profileReads.push(data.params.args[0]);
        }
    });
    await p.goto(`${base}/web/login?db=${db}`,{timeout:60000});
    await p.locator('[name=login]').fill(credential.login);
    await p.locator('[name=password]').fill(credential.password);
    await p.locator('button[type=submit]').click();
    await p.locator('.o_web_client').waitFor({timeout:120000});
    const session=await (await context.request.post(`${base}/web/session/get_session_info`,{
        data:{jsonrpc:'2.0',method:'call',params:{}},
    })).json();
    const uid=session.result.uid;
    const [profile]=await rpc(context,'res.users','read',[[uid],['name','phone','email','tz','lang']]);
    await overview(p);
    const footer=p.locator('.o_tp_kd_sb_foot');
    const account=footer.locator('.o_tp_kd_sb_account'), prefs=footer.locator('.o_tp_kd_sb_prefs');
    const a=await account.boundingBox(),d=await prefs.boundingBox();
    check(alias+' account directly above display preferences',a.y+a.height<=d.y+1);
    check(alias+' accessible account name',await account.getAttribute('aria-label')==='Tài khoản');
    check(alias+' no horizontal overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await shot(p,alias+'-desktop');
    const route=p.url();await open(p,true);
    check(alias+' native own record',profileReads.at(-1)?.length===1&&profileReads.at(-1)[0]===uid);
    check(alias+' own profile name',await p.locator('.o_dialog [name=name] input').inputValue()===profile.name);
    check(alias+' profile contact fields',await p.locator('.o_dialog [name=email] input').count()===1&&await p.locator('.o_dialog [name=phone] input').count()===1);
    check(alias+' no permission group editor',await p.locator('.o_dialog [name=group_ids]').count()===0);
    check(alias+' dialog keeps route',p.url()===route);
    await p.locator('.o_dialog button[name=page_security]').click();
    check(alias+' native change password',await p.locator('.o_dialog button[name=preference_change_password]').isVisible());
    await shot(p,alias+'-security');await cancel(p);
    check(alias+' cancel leaves profile unchanged',JSON.stringify((await rpc(context,'res.users','read',[[uid],['name','phone','email','tz','lang']]))[0])===JSON.stringify(profile));

    // Existing display options still work; rail keeps an accessible account icon.
    await prefs.click();await p.locator('.o_tp_kd_prefs').waitFor();
    check(alias+' existing display preferences',await p.getByRole('radio',{name:'Gọn',exact:true}).isVisible());
    await p.keyboard.press('Escape');
    await p.getByRole('button',{name:'Thu gọn thanh bên',exact:true}).click();
    await p.locator('.o_tp_kd_sidebar.is-rail').waitFor();await open(p);
    check(alias+' rail own profile',profileReads.at(-1)[0]===uid);await cancel(p);
    await p.getByRole('button',{name:'Mở rộng thanh bên',exact:true}).click();

    await p.setViewportSize({width:390,height:844});
    await p.locator('.o_tp_kd_menu_toggle').click();await shot(p,alias+'-mobile');
    await open(p);
    check(alias+' mobile drawer closes',await p.locator('.o_tp_kd_sidebar.is-drawer,.o_tp_kd_backdrop').count()===0);
    await p.locator('.o_dialog [name=phone] input').focus();await p.keyboard.press('Tab');
    check(alias+' modal keyboard focus',await p.evaluate(()=>Boolean(document.activeElement.closest('.o_dialog'))));
    check(alias+' mobile own profile',profileReads.at(-1)[0]===uid);
    check(alias+' mobile no overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await shot(p,alias+'-mobile-profile');await cancel(p);
    await p.waitForFunction(()=>document.activeElement?.classList.contains('o_tp_kd_menu_toggle'));
    check(alias+' mobile focus returns to menu',await p.locator('.o_tp_kd_menu_toggle').evaluate(el=>el===document.activeElement));

    if(target==='clone'&&alias==='support') {
     await p.setViewportSize({width:1440,height:1000});
     await open(p);const phone=p.locator('.o_dialog [name=phone] input');
     await phone.fill('0900001001');await cancel(p);
     check('clone discard modified phone',(await rpc(context,'res.users','read',[[uid],['phone']]))[0].phone===profile.phone);
     try {
      await open(p);await phone.fill('0900001001');
      await saveProfile(p);
      await open(p);check('clone save persists after reload',await phone.inputValue()==='0900001001');
      await phone.fill(profile.phone||'');await saveProfile(p);
     } finally {
      // Clone only: always restore original field if a browser assertion fails.
      if((await rpc(context,'res.users','read',[[uid],['phone']]))[0].phone!==profile.phone)
       await rpc(context,'res.users','write',[[uid],{phone:profile.phone}]);
     }
     check('clone original phone restored',(await rpc(context,'res.users','read',[[uid],['phone']]))[0].phone===profile.phone);
     // Own account dialog must preserve the unsaved dossier underneath it.
     await p.locator('.o_tp_kd_sidebar').getByRole('link',{name:'Năng lực và chứng chỉ',exact:true}).click();
     await p.locator('.o_list_view .o_list_renderer').waitFor({timeout:60000});
     await p.locator('.o_list_button_add').click();await p.locator('.o_action_manager .o_form_view').waitFor();
     const name=p.locator('.o_action_manager [name=name] input');
     await name.fill('ACCOUNT001 unsaved clone');await open(p);await cancel(p);
     check('clone dirty dossier remains intact',await name.inputValue()==='ACCOUNT001 unsaved clone');
     // No save: closing this isolated context discards the new dossier.
    }
   } catch(e) {if(current)await shot(current,alias+'-failure').catch(()=>{});throw e;}
   finally {await context.close();current=null;}
  }
  check('source unchanged during browser run',JSON.stringify(sourceHashes())===JSON.stringify(initialHashes));
 } catch(e) {
  failures.push(redact(e.stack||e.message));
  if(current&&!current.isClosed())await shot(current,'failure').catch(()=>{});
 } finally {
  await browser.close();
  const result={target,passed:failures.length||errors.length?0:checks.length,checks,failures,errors,source_hashes:initialHashes};
  fs.writeFileSync(path.join(local,`${target}-browser.json`),JSON.stringify(result,null,2));
  console.log(JSON.stringify({target,passed:result.passed,failures,errors}));
  process.exitCode=failures.length||errors.length?1:0;
 }
})();
