/* Five isolated native sessions, private credentials/evidence; dev is read-only. */
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),local=path.join(root,'.local/kd-access002');
const target=process.argv[2]||'clone',before=process.argv.includes('--before');
assert(['clone','dev'].includes(target));
const base=`http://127.0.0.1:${target==='dev'?18069:19289}`;
const delta=JSON.parse(fs.readFileSync(path.join(root,'.local/kd-access001/dev-delta.json')));
const creds=JSON.parse(fs.readFileSync(path.join(root,'.local/kd-access001/dev-credentials.json')));
const shots=path.join(local,'shots',target,before?'before':'after');fs.mkdirSync(shots,{recursive:true});
const checks=[],errors=[],failures=[];
function sourceHashes(){const all={};for(const m of ['tp_kd_workspace','tp_web_home']){const dir=path.join(root,target==='clone'?'.local/kd-access002/source/custom_addons':'custom_addons',m);const hashes={};function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){if(e.name==='__pycache__'||e.name.endsWith('.pyc'))continue;const f=path.join(d,e.name);if(e.isDirectory())walk(f);else hashes[path.relative(dir,f).split(path.sep).join('/')]=crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');}}walk(dir);all[m]=hashes;}return all;}
const initialHashes=sourceHashes();
const fixture=target==='clone'&&!before?JSON.parse(fs.readFileSync(path.join(local,'fixture.json'))):null;
const rights=fixture?JSON.parse(fs.readFileSync(path.join(local,'clone-delta.json'))):null;
const check=(n,b)=>{assert(b,n);checks.push(n);};
async function rpc(c,m,f,a=[],kw={}){return(await c.request.post(`${base}/web/dataset/call_kw/${m}/${f}`,{data:{jsonrpc:'2.0',method:'call',params:{model:m,method:f,args:a,kwargs:kw}}})).json();}
async function ok(...a){const r=await rpc(...a);assert(!r.error,r.error?.data?.message);return r.result;}
async function shot(p,n){await p.screenshot({path:path.join(shots,n+'.png'),fullPage:true,animations:'disabled'});}
async function ready(p,selector){try{await p.locator(selector).first().waitFor({timeout:60000});}catch(e){await shot(p,'navigation-retry-'+Date.now());fs.writeFileSync(path.join(shots,'navigation-retry.txt'),await p.locator('body').innerText());await p.reload({timeout:120000});await p.locator(selector).first().waitFor({timeout:60000});}}
async function list(p,a){const id=a==='contracts'?'tp_contract.action_tp_contracts_list':`tp_kd_workspace.action_${a}`;await p.goto(`${base}/odoo/action-${id}`,{timeout:120000});await ready(p,'.o_list_renderer');}
(async()=>{const b=await chromium.launch({headless:true});const cs=[];try{
for(const [alias,row] of Object.entries(delta.users)){
 const c=await b.newContext({viewport:{width:1440,height:1000},locale:'vi-VN'});cs.push(c);const p=await c.newPage();
 p.on('pageerror',e=>errors.push(alias+': '+e.message));
 p.on('console',m=>{if(m.type()==='error')errors.push(alias+': '+m.text());});
 await p.goto(`${base}/web/login?db=${target==='dev'?'tp_tanphat_dev':'tp_tanphat_kdaccess002_20261109'}`);
 await p.locator('[name=login]').fill(creds[alias].login);await p.locator('[name=password]').fill(creds[alias].password);
 await p.locator('button[type=submit]').click();await p.locator('.o_web_client').waitFor({timeout:120000});
 await p.locator('.o_tp_web_home').waitFor({timeout:60000});await shot(p,alias+'-home');
 check(alias+' project scope',JSON.stringify((await ok(c,'project.project','search', [[]])).sort((a,b)=>a-b))===JSON.stringify([...row.projects].sort((a,b)=>a-b)));
 if(before){check(alias+' CRM absent',Boolean((await rpc(c,'crm.lead','search_read',[[]],{fields:['name']})).error));continue;}
 await list(p,'opportunities');await shot(p,alias+'-crm-list');
 check(alias+' CRM scope',(await ok(c,'crm.lead','search_read',[[]],{fields:['tp_project_id']})).every(r=>!r.tp_project_id||row.projects.includes(r.tp_project_id[0])));
 check(alias+' create capability',(await ok(c,'crm.lead','get_kd_ui_permissions')).create);
 const old=await ok(c,'crm.lead','search',[[['user_id','!=',row.id]]],{limit:1});
 if(old.length){
  await p.goto(`${base}/odoo/action-tp_kd_workspace.action_opportunities/${old[0]}`);await ready(p,'.o_form_view');await shot(p,alias+'-crm-form');
  check(alias+' old owner cannot prepare',!await p.getByRole('button',{name:'Chuẩn bị hồ sơ',exact:true}).isVisible().catch(()=>false));
 }
 if(fixture){
  const f=fixture[alias];
  await p.goto(`${base}/odoo/action-tp_kd_workspace.action_opportunities/${f.lead_id}`);
  await ready(p,'.o_form_view');
  const prepare=p.getByRole('button',{name:'Chuẩn bị hồ sơ',exact:true});
  if(await prepare.isVisible()){await Promise.all([p.waitForResponse(r=>r.url().includes('/web/dataset/call_button')),prepare.click()]);}
  await p.waitForFunction(()=>!document.querySelector('.o_loading_indicator'));
  let [state]=await ok(c,'crm.lead','read',[[f.lead_id],['kd_bid_state','kd_can_submit']]);
  check(alias+' actual prepare UI',state.kd_bid_state==='preparation'||state.kd_bid_state==='submitted');
  if(alias==='support'){
   check('support submit hidden',!await p.getByRole('button',{name:'Khai báo đã nộp',exact:true}).isVisible().catch(()=>false));
   check('support direct submit denied',Boolean((await rpc(c,'crm.lead','action_kd_record_submission',[[f.lead_id]])).error));
  }else if(state.kd_bid_state==='preparation'){
   await Promise.all([p.waitForResponse(r=>r.url().includes('/web/dataset/call_button')),p.getByRole('button',{name:'Khai báo đã nộp',exact:true}).click()]);
   [state]=await ok(c,'crm.lead','read',[[f.lead_id],['kd_bid_state']]);check(alias+' actual submit UI',state.kd_bid_state==='submitted');
  }
  const file=await c.request.get(`${base}/web/content/${f.attachment_id}?download=true`);
  check(alias+' direct CRM file policy',alias==='support'?[403,404].includes(file.status()):file.status()===200&&(await file.text()).includes('KD002_SYNTHETIC'));
  const tokenFile=await c.request.get(`${base}/web/content/${f.attachment_id}?download=true&access_token=KD002-synthetic-${alias}`);
  check(alias+' token CRM file policy',alias==='support'?[403,404].includes(tokenFile.status()):tokenFile.status()===200);
  const raw=await rpc(c,'ir.attachment','read',[[f.attachment_id],['raw']]);check(alias+' CRM file RPC policy',alias==='support'?Boolean(raw.error):!raw.error);
  const exported=await ok(c,'crm.lead','export_data',[[f.lead_id],['name','kd_bid_state']]);check(alias+' metadata export works',exported.datas.length===1);
  for(const method of ['search_count','search'])check(alias+' money domain enforced',alias==='support'?Boolean((await rpc(c,'crm.lead',method,[[['expected_revenue','>',-1]]])).error):!(await rpc(c,'crm.lead',method,[[['expected_revenue','>',-1]]])).error);
  await shot(p,alias+'-own-CRM-action');
  if(alias==='head'){
   const phase=n=>{const r=spawnSync(path.join(root,'.venv/Scripts/python.exe'),['-X','utf8',path.join(root,'scripts/kd_access002.py'),'phase','--label',n],{cwd:root,encoding:'utf8',windowsHide:true});assert(r.status===0,'owned lifecycle phase failed');};
   try{for(const n of ['revoked','expired','unassigned']){
    phase(n);
    check('head live '+n+' money blocked',Boolean((await rpc(c,'crm.lead','read',[[f.lead_id],['expected_revenue']])).error));
    check('head live '+n+' file blocked',[403,404].includes((await c.request.get(`${base}/web/content/${f.attachment_id}?download=true`)).status()));
    check('head live '+n+' token file blocked',[403,404].includes((await c.request.get(`${base}/web/content/${f.attachment_id}?download=true&access_token=KD002-synthetic-head`)).status()));
    if(n==='revoked'||n==='expired')await p.waitForFunction(()=>document.querySelector('[name=kd_money_display]')?.textContent.includes('Không có quyền xem tiền'),null,{timeout:15000});
   }}finally{phase('normal');}
   check('head restored file same session',(await c.request.get(`${base}/web/content/${f.attachment_id}?download=true`)).status()===200);
  }
  if(!f.preproject_id){f.preproject_id=await ok(c,'crm.lead','create',[[{name:'KD002 Synthetic pre-project '+alias,type:'opportunity',company_id:row.company_id,user_id:row.id,team_id:rights.team_id,kd_source:'Synthetic HTTP',kd_scope:'Synthetic HTTP',kd_checklist:'Synthetic HTTP',kd_deadline:'2030-01-01',kd_receipt:'Synthetic unverified'}]]);if(Array.isArray(f.preproject_id))f.preproject_id=f.preproject_id[0];fs.writeFileSync(path.join(local,'fixture.json'),JSON.stringify(fixture,null,2));}
  let [pre]=await ok(c,'crm.lead','read',[[f.preproject_id],['user_id','tp_project_id','kd_bid_state']]);check(alias+' pre-project own native team',pre.user_id[0]===row.id&&!pre.tp_project_id);
  if(pre.kd_bid_state==='identified')await ok(c,'crm.lead','action_kd_prepare',[[f.preproject_id]]);
  if(alias==='support')check('support pre-project submit denied',Boolean((await rpc(c,'crm.lead','action_kd_record_submission',[[f.preproject_id]])).error));
  else if(pre.kd_bid_state!=='submitted')await ok(c,'crm.lead','action_kd_record_submission',[[f.preproject_id]]);
  check(alias+' pre-project money denied',Boolean((await rpc(c,'crm.lead','read',[[f.preproject_id],['expected_revenue']])).error));
  check(alias+' pre-project only assigned owner',(await ok(c,'crm.lead','search_read',[[['tp_project_id','=',false]]],{fields:['user_id']})).every(r=>r.user_id[0]===row.id));
 }
 await p.setViewportSize({width:390,height:844});await shot(p,alias+'-crm-mobile');
 check(alias+' mobile no page overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await p.setViewportSize({width:1440,height:1000});
 const dashboard=await ok(c,'tp.kd.overview','get_kd_dashboard');check(alias+' CRM dashboard available',dashboard.readable.opportunities===true);
 check(alias+' correct project KPI',dashboard.kpis.projects===row.projects.length);
 await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`);await ready(p,'.o_tp_kd_ov');await shot(p,alias+'-overview');
 const report=p.locator('.o_tp_kd_sb_leaf').filter({hasText:'Báo cáo KH-KD'});
 if(!await report.isVisible())await p.getByRole('button',{name:'Báo cáo và quản trị',exact:false}).click();
 await report.click();await ready(p,'.o_tp_kd_ov');check(alias+' native reports entry uses scoped overview',await p.locator('.o_tp_kd_ov').isVisible());
 await shot(p,alias+'-reports');
 await p.locator('.o_tp_kd_sb_account').click();await ready(p,'.o_dialog .o_form_view');
 check(alias+' own account dialog',await p.locator('.o_dialog [name=name] input').count()===1&&await p.locator('.o_dialog [name=group_ids]').count()===0);
 await p.locator('.o_dialog button[name=preference_cancel]').click();await p.locator('.o_dialog').waitFor({state:'hidden'});
 for(const a of ['projects','tasks','contracts','allocations','productions','acceptances','plans','payments','credentials','obligations']){
  await list(p,a);check(alias+' native list '+a,await p.locator('.o_list_renderer').isVisible());
 }
 const money=await rpc(c,'crm.lead','search_read',[[['tp_project_id','!=',false]]],{fields:['name','expected_revenue']});
 check(alias+' money policy',alias==='support'?Boolean(money.error):!money.error);
 const company=p.locator('.o_switch_company_menu .oe_topbar_name');check(alias+' company label hidden',!await company.isVisible().catch(()=>false));
 check(alias+' company icon retained',await p.locator('.o_switch_company_menu [data-icon=business]').isVisible());
 await shot(p,alias+'-navbar');
}
check('five separate sessions',cs.length===5);
check('source stable through browser tests',JSON.stringify(sourceHashes())===JSON.stringify(initialHashes));
}catch(e){failures.push(e.message);}finally{for(const c of cs)await c.close();await b.close();const r={ok:!failures.length&&!errors.length,target,before,checks,passed:checks.length,failures,errors,source_hashes:initialHashes};fs.writeFileSync(path.join(local,`${target}-${before?'before':'browser'}.json`),JSON.stringify(r,null,2));console.log(JSON.stringify({ok:r.ok,passed:r.passed,failures:failures.length,errors:errors.length}));process.exitCode=r.ok?0:1;}})();
