/* Owned KD-UI-007 browser checks. Dev modes only read records. */
const {chromium} = require('../frontend/node_modules/playwright');
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..'), local = path.join(root, '.local/kd-ui007');
const target = process.argv[2] || 'clone', mode = process.argv[3] || 'before';
assert(['clone','dev'].includes(target));
assert(target === 'clone' || ['before','verify','regression'].includes(mode));
const owner = JSON.parse(fs.readFileSync(path.join(local,'owner.json')));
assert(owner.database === 'tp_tanphat_kdui007_20261107' && owner.http_port === 18889 && owner.rehearsal_passed);
const db = target === 'dev' ? 'tp_tanphat_dev' : owner.database;
const base = `http://127.0.0.1:${target === 'dev' ? 18069 : owner.http_port}`;
const actors = JSON.parse(fs.readFileSync(path.join(root,'.local/kd-native001/dataset/dev/credentials.json')));
const out = path.join(local,'shots',`${target}-${mode}`); fs.mkdirSync(out,{recursive:true});
const results=[],failures=[],errors=[];
function sourceHashes() {
 const folder=path.join(root,target==='dev'?'custom_addons/tp_kd_workspace':'.local/kd-ui007/source/custom_addons/tp_kd_workspace');
 const hashes={}; const walk=d=>{for(const e of fs.readdirSync(d,{withFileTypes:true})) {
  if(e.name==='__pycache__'||e.name.endsWith('.pyc'))continue;
  const p=path.join(d,e.name);if(e.isDirectory())walk(p);else hashes[path.relative(folder,p).replaceAll('\\','/')]=crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 }};walk(folder);return hashes;
}
const initialHashes=sourceHashes();
const check=(n,c,d)=>{if(c)results.push(n);else failures.push(`${n}: ${JSON.stringify(d)}`);};
async function login(browser,key,options={}) {
 const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'vi-VN',...options});
 const response=await context.request.post(`${base}/web/session/authenticate`,{data:{jsonrpc:'2.0',method:'call',params:{db,...actors[key]}}});
 assert((await response.json()).result?.uid,'login failed');return context;
}
async function rpc(context,model,method,args=[],kwargs={}) {
 return (await context.request.post(`${base}/web/dataset/call_kw/${model}/${method}`,{data:{jsonrpc:'2.0',method:'call',params:{model,method,args,kwargs}}})).json();
}
async function ok(...args){const b=await rpc(...args);assert(!b.error,b.error?.data?.message);return b.result;}
function watch(p){p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});}
async function settle(p){await p.waitForFunction(()=>!document.querySelector('.o_loading_indicator'),null,{timeout:8000}).catch(()=>{});await p.waitForFunction(()=>{const list=document.querySelector('.o_action_manager > .o_list_view');return !list||Boolean(list.querySelector('.o_list_renderer'));},null,{timeout:15000});await p.waitForTimeout(220);}
async function shot(p,n,full=false){await p.screenshot({path:path.join(out,`${n}.png`),fullPage:full,animations:'disabled',timeout:15000});}
async function openList(p,a){try{
 if(a==='tp_contract.action_tp_contracts'){
  await p.goto(`${base}/odoo/action-tp_kd_workspace.action_projects`,{timeout:120000});await p.locator('.o_list_view').first().waitFor({timeout:60000});await settle(p);
  await p.locator('.o_tp_kd_sidebar').waitFor({state:'attached'});
  const drawer=p.locator('.o_tp_kd_menu_toggle');if(await drawer.isVisible()&&await drawer.getAttribute('aria-expanded')!=='true')await drawer.click();
  const leaf=p.locator('.o_tp_kd_sb_leaf').filter({hasText:'Hợp đồng và phụ lục'});
  if(!await leaf.isVisible())await leaf.locator('xpath=ancestor::li[contains(@class,"o_tp_kd_sb_group")]').locator('.o_tp_kd_sb_group_btn').click();
  const previous=await p.locator('.o_action_manager > .o_action').first().elementHandle();
  await leaf.click({timeout:10000}).catch(async e=>{console.log('contract entry dialog',await p.locator('.modal').allTextContents());throw e;});await p.waitForFunction(e=>!e.isConnected,previous);
 }else await p.goto(`${base}/odoo/action-${a}`,{timeout:120000});
 await p.locator('.o_list_view').first().waitFor({timeout:60000});await settle(p);
 }catch(e){await shot(p,`navigation-failure-${Date.now()}`);fs.writeFileSync(path.join(out,'navigation-failure.txt'),await p.locator('body').innerText());throw e;}
}
async function openFirst(p){await p.locator('.o_data_row .o_data_cell').first().click();await p.locator('.o_action_manager .o_form_view').waitFor({timeout:30000});await settle(p);}
const LEAVES=[['opportunities','tp_kd_workspace.action_opportunities'],['projects','tp_kd_workspace.action_projects'],['contracts','tp_contract.action_tp_contracts'],['tasks','tp_kd_workspace.action_tasks'],['allocations','tp_kd_workspace.action_allocations'],['productions','tp_kd_workspace.action_productions'],['acceptances','tp_kd_workspace.action_acceptances'],['payments','tp_kd_workspace.action_payments'],['plans','tp_kd_workspace.action_plans'],['credentials','tp_kd_workspace.action_credentials'],['obligations','tp_kd_workspace.action_obligations']];
(async()=>{
 const browser=await chromium.launch({headless:true});
 const ctx={browser,root,local,base,db,target,mode,actors,out,results,errors,check,login,rpc,ok,watch,settle,shot,openList,openFirst,LEAVES,
 tableTokens:{line:'rgb(216, 227, 239)',head:'rgb(234, 241, 248)',cellLine:'rgba(0, 0, 0, 0)'}};
 try {
  if(mode==='before') {
   for(const width of [1440,390]) {
    const c=await login(browser,'editor',{viewport:{width,height:1000}});const p=await c.newPage();watch(p);
    for(const [name,a] of LEAVES){await openList(p,a);await shot(p,`list-${name}-${width}`);if(await p.locator('.o_data_row').count()){await openFirst(p);await shot(p,`form-${name}-${width}`,true);}}
    await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`,{timeout:120000});await p.locator('.o_tp_kd_ov').waitFor({timeout:60000});await settle(p);await shot(p,`overview-${width}`,true);
    await c.close();
   }
   check('before all 11 lists/forms and overview captured',true);
  } else if(mode==='hoot') {
   const c=await login(browser,'editor'),p=await c.newPage(),logs=[];watch(p);p.on('console',m=>logs.push(m.text()));
   await p.goto(`${base}/web/tests?headless&debug=assets&filter=tp_kd_workspace`,{timeout:180000});
   const end=Date.now()+240000;while(!logs.some(l=>/Test suite succeeded|Some tests failed/i.test(l))&&Date.now()<end)await p.waitForTimeout(500);
   fs.writeFileSync(path.join(out,'hoot.txt'),await p.locator('body').innerText());fs.writeFileSync(path.join(out,'console.txt'),logs.join('\n'));
   check('HOOT passed',logs.some(l=>/Test suite succeeded/i.test(l)),logs.slice(-8));await c.close();
  } else if(mode==='regression') {
   await require('./kd_ui003_ui_after.cjs')(ctx);
  } else if(mode==='extra') {
   await require('./kd_ui007_extra.cjs')(ctx);
  } else if(mode==='zoom') {
   await require('./kd_ui007_zoom.cjs')({...ctx,chromium});
  } else {
   await require('./kd_ui007_checks.cjs')(ctx);
  }
 } catch(e){failures.push(e.stack);} finally {
  await browser.close();
  const r={target,mode,passed:results.length,failures,errors,source_hashes:initialHashes};
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(r,null,2));
  if(target==='clone'&&['after','hoot','regression','zoom'].includes(mode))fs.writeFileSync(path.join(local,mode==='after'?'browser-result.json':`${mode}-result.json`),JSON.stringify(r,null,2));
  console.log(JSON.stringify({passed:r.passed,failures,errors:errors.map(e=>e.slice(0,400))}));process.exitCode=failures.length||errors.length?1:0;
 }
})();
