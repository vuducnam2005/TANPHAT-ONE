/* Five isolated sessions; dev mode only navigates/reads. No credential output or traces. */
const { chromium } = require('../frontend/node_modules/playwright');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..'), local = path.join(root, '.local/kd-access001');
const target = process.argv[2] || 'clone';
assert(['clone', 'dev'].includes(target));
const owner = JSON.parse(fs.readFileSync(path.join(local, 'owner.json')));
assert(owner.database === 'tp_tanphat_kdaccess001_20261108' && owner.http_port === 18989 && owner.rehearsal_passed);
const delta = JSON.parse(fs.readFileSync(path.join(local, `${target}-delta.json`)));
const credentials = JSON.parse(fs.readFileSync(path.join(local, `${target}-credentials.json`)));
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : 18989}`;
const out = path.join(local, 'shots', target); fs.mkdirSync(out, {recursive:true});
const checks = [], failures = [], errors = [], contexts = [];
const check = (name, condition) => {assert(condition, name); checks.push(name);};
async function rpc(c, model, method, args=[], kwargs={}) {
  return (await c.request.post(`${base}/web/dataset/call_kw/${model}/${method}`, {data:{jsonrpc:'2.0',method:'call',params:{model,method,args,kwargs}}})).json();
}
async function ok(...args) {const result=await rpc(...args); assert(!result.error, result.error?.data?.message); return result.result;}
async function shot(p, name) {await p.screenshot({path:path.join(out,name+'.png'),animations:'disabled',fullPage:true});}
async function list(p, action) {
  await p.goto(`${base}/odoo/action-${action}`, {timeout:120000});
  try {await p.locator('.o_list_view .o_list_renderer').first().waitFor({timeout:60000});}
  catch(e) {
    await shot(p,'navigation-retry-'+Date.now());
    fs.writeFileSync(path.join(out,'navigation-retry.txt'),await p.locator('body').innerText());
    await p.reload({timeout:120000});
    await p.locator('.o_list_view .o_list_renderer').first().waitFor({timeout:60000});
  }
  await p.waitForFunction(()=>!document.querySelector('.o_loading_indicator'),null,{timeout:15000});
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  for (const [alias, row] of Object.entries(delta.users)) {
   const c=await browser.newContext({viewport:{width:1440,height:1000},locale:'vi-VN'}); contexts.push(c);
   const p=await c.newPage();
   p.on('pageerror',e=>errors.push(alias+': '+e.message));
   p.on('console',m=>{if(m.type()==='error') errors.push(alias+': '+m.text());});
   await p.goto(`${base}/web/login?db=${delta.identity.database}`,{timeout:60000});
   await p.locator('input[name="login"]').fill(credentials[alias].login);
   await p.locator('input[name="password"]').fill(credentials[alias].password);
   await p.locator('button[type="submit"]').click();
   await p.locator('.o_web_client').waitFor({timeout:120000});
   await p.locator('.o_tp_web_home').waitFor({timeout:60000});
   check(alias+' native Home',await p.locator('.o_tp_web_home_brand').innerText()==='TANPHAT ONE');
   check(alias+' no admin home',!(await p.locator('.o_tp_web_home').innerText()).includes('Quản trị hệ thống'));
   const session=await (await c.request.post(`${base}/web/session/get_session_info`,{data:{jsonrpc:'2.0',method:'call',params:{}}})).json();
   check(alias+' separate identity',session.result.uid===row.id);
   await shot(p,alias+'-home');
   const projects=await ok(c,'project.project','search_read',[[]],{fields:['id','tp_code']});
   check(alias+' exact RPC project scope',JSON.stringify(projects.map(r=>r.id).sort((a,b)=>a-b))===JSON.stringify([...row.projects].sort((a,b)=>a-b)));
   const relations=await ok(c,'project.project','name_search',[],{name:'',limit:100});
   check(alias+' relation scope',relations.every(r=>row.projects.includes(r[0])));
   const crm=await rpc(c,'crm.lead','search_read',[[]],{fields:['name','expected_revenue']});
   check(alias+' CRM RPC denied',Boolean(crm.error));
   const dashboard=await ok(c,'tp.kd.overview','get_kd_dashboard',[]);
   check(alias+' dashboard project scope',dashboard.kpis.projects===row.projects.length);
   check(alias+' opportunity unavailable',dashboard.readable.opportunities===false);
   check(alias+' dashboard dropdown scope',dashboard.options.projects.every(r=>row.projects.includes(r.id)));
   const create=dashboard.create.map(r=>r.kind);
   check(alias+' no new project/task/opportunity',!create.some(r=>['project','task','opportunity'].includes(r)));
   if(alias==='head') check('head no prepare button',create.length===0);
   if(alias==='support') check('support only credential prepare',create.length===1&&create[0]==='credential');
   if(alias==='planning') check('planning no payment/acceptance/contract',!create.some(r=>['payment','acceptance','contract'].includes(r)));
   await list(p,'tp_kd_workspace.action_projects');
   check(alias+' project native rows',await p.locator('.o_data_row').count()===row.projects.length);
   await shot(p,alias+'-projects');
   await p.locator('.o_data_row .o_data_cell').first().click();
   await p.locator('.o_action_manager .o_form_view').waitFor({timeout:30000});
   check(alias+' no assignment admin',!(await p.locator('.o_form_view').innerText()).includes('Phân công'));
   await shot(p,alias+'-project-form');
   await list(p,'tp_kd_workspace.action_credentials');
   const perms=await ok(c,'tp.credential','get_kd_ui_permissions',[]);
   check(alias+' credential prepare role',perms.create===(alias!=='head'));
   check(alias+' New matches permission',await p.locator('.o_list_button_add').isVisible().catch(()=>false)===perms.create);
   if(await p.locator('.o_data_row').count()) {
    await p.locator('.o_data_row .o_data_cell').first().click();
    await p.locator('.o_action_manager .o_form_view').waitFor({timeout:30000});
    check(alias+' existing dossier no owner submit',await p.getByRole('button',{name:'Gửi rà soát',exact:true}).isVisible().catch(()=>false)===false);
    await shot(p,alias+'-credential-form');
   }
   if(alias==='support') {
    for(const model of ['tp.contract.line.amount','tp.contract.submission.amount','tp.allocation.amount','tp.periodic.plan.amount']) {
     check('support RPC no money '+model,await ok(c,model,'search_count',[[]])===0);
    }
    check('support financial files hidden',await ok(c,'tp.contract.document','search_count',[[['confidentiality','=','financial']]])===0);
   }
   const outside=Object.values(delta.users).flatMap(r=>r.projects).find(id=>!row.projects.includes(id));
   if(outside) check(alias+' known outside ID denied',Boolean((await rpc(c,'project.project','read',[[outside],['name','tp_code']])).error));
   await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`,{timeout:120000});
   await p.locator('.o_tp_kd_ov').waitFor({timeout:60000}); await shot(p,alias+'-overview');
   check(alias+' no horizontal page overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  }
  check('five simultaneous sessions',contexts.length===5);
  for(let i=0;i<contexts.length;i++){
   const alias=Object.keys(delta.users)[i];
   const b=await (await contexts[i].request.post(`${base}/web/session/get_session_info`,{data:{jsonrpc:'2.0',method:'call',params:{}}})).json();
   check(alias+' session remains separate',b.result.uid===delta.users[alias].id);
  }
 } catch(e) {failures.push(e.message);} finally {
  for(const c of contexts) await c.close(); await browser.close();
  const result={target,passed:failures.length===0&&errors.length===0?checks.length:0,checks,failures,errors};
  fs.writeFileSync(path.join(local,`${target}-browser.json`),JSON.stringify(result,null,2));
  console.log(JSON.stringify({target,passed:result.passed,failures,errors}));
  process.exitCode=failures.length||errors.length?1:0;
 }
})();
