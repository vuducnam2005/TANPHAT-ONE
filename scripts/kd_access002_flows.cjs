/* Native CRM create/edit/money/prepare/submit on owned clone only. */
const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:19289',out=path.join(root,'.local/kd-access002');
const owner=JSON.parse(fs.readFileSync(path.join(out,'owner.json')));
assert(owner.database==='tp_tanphat_kdaccess002_20261109'&&owner.http_port===19289&&owner.rehearsal_passed);
const delta=JSON.parse(fs.readFileSync(path.join(root,'.local/kd-access001/dev-delta.json')));
const creds=JSON.parse(fs.readFileSync(path.join(root,'.local/kd-access001/dev-credentials.json')));
const checks=[],errors=[],records={};let p;
function sourceHashes(){const r={};for(const m of ['tp_kd_workspace','tp_web_home']){r[m]={};const dir=path.join(out,'source/custom_addons',m);function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){if(e.name==='__pycache__'||e.name.endsWith('.pyc'))continue;const f=path.join(d,e.name);if(e.isDirectory())walk(f);else r[m][path.relative(dir,f).split(path.sep).join('/')]=crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');}}walk(dir);}return r;}
const initialHashes=sourceHashes();
async function rpc(c,m,f,a=[],kw={}){const r=await(await c.request.post(`${base}/web/dataset/call_kw/${m}/${f}`,{data:{jsonrpc:'2.0',method:'call',params:{model:m,method:f,args:a,kwargs:kw}}})).json();assert(!r.error,r.error?.data?.message);return r.result;}
const check=(s,b)=>{assert(b,s);checks.push(s);};
async function shot(name){await p.screenshot({path:path.join(out,'shots/clone/after',name+'.png'),fullPage:true,animations:'disabled'});}
async function field(n,v){const x=p.locator(`.o_field_widget[name="${n}"] input, .o_field_widget[name="${n}"] textarea`).first();await x.fill(v);await x.press('Tab');}
async function button(n){await Promise.all([p.waitForResponse(r=>r.url().includes('/web/dataset/call_button')),p.getByRole('button',{name:n,exact:true}).click()]);}
(async()=>{const b=await chromium.launch({headless:true});let ok=false;try{
for(const [alias,row] of Object.entries(delta.users)){
 const c=await b.newContext({viewport:{width:1440,height:1000},locale:'vi-VN'});p=await c.newPage();
 p.on('pageerror',e=>errors.push(alias+': '+e.message));p.on('console',m=>{if(m.type()==='error')errors.push(alias+': '+m.text());});
 await p.goto(`${base}/web/login?db=${owner.database}`);await p.locator('[name=login]').fill(creds[alias].login);await p.locator('[name=password]').fill(creds[alias].password);await p.locator('button[type=submit]').click();await p.locator('.o_tp_web_home').waitFor({timeout:120000});
 await p.goto(`${base}/odoo/action-tp_kd_workspace.action_opportunities`);await p.locator('.o_list_button_add').waitFor({timeout:60000});await p.locator('.o_list_button_add').click();await p.locator('.o_form_view').waitFor();
 const name='KD002 UI create '+alias+' '+Date.now();await field('name',name);await field('kd_source','Synthetic native UI');
 const [project]=await rpc(c,'project.project','read',[[row.projects[0]],['name','partner_id']]);
 const partner=p.locator('[name=partner_id] input');await partner.fill(project.partner_id[1].slice(0,24));await p.locator('.o-autocomplete--dropdown-item').filter({hasText:project.partner_id[1]}).first().click();
 const relation=p.locator('[name=tp_project_id] input');await relation.fill(project.name.slice(0,28));await p.locator('.o-autocomplete--dropdown-item').filter({hasText:project.name}).first().click();
 await field('kd_deadline','01/01/2030');await field('kd_scope','Synthetic native scope');
 await p.getByRole('tab',{name:'Checklist hồ sơ',exact:true}).click();await field('kd_checklist','Synthetic native checklist');await field('kd_receipt','Synthetic receipt, unverified');
 await p.locator('.o_form_button_save').click();
 await p.locator('.o_form_button_save').waitFor({state:'hidden'});
 const [lead]=await rpc(c,'crm.lead','search_read',[[['name','=',name]]],{fields:['kd_bid_state','user_id','kd_source','kd_scope','kd_checklist','kd_deadline']});assert(lead);
 records[alias]=lead.id;check(alias+' native create saved owner/scope',lead.user_id[0]===row.id&&lead.kd_deadline==='2030-01-01'&&lead.kd_scope==='Synthetic native scope');
 await field('kd_source','Synthetic native edited');await p.locator('.o_form_button_save').click();
 await p.locator('.o_form_button_save').waitFor({state:'hidden'});
 check(alias+' native draft edit saved',(await rpc(c,'crm.lead','read',[[lead.id],['kd_source']]))[0].kd_source==='Synthetic native edited');
 const money=p.getByRole('button',{name:'Sửa giá trị dự kiến',exact:true});
 check(alias+' native money edit capability',await money.isVisible().catch(()=>false)===['deputy','project_lead','planning'].includes(alias));
 if(['deputy','project_lead','planning'].includes(alias)){
  await money.click();await p.locator('.o_dialog [name=amount] input').fill('1234567');await button('Lưu giá trị dự kiến');await p.locator('.o_dialog').waitFor({state:'hidden'});
  check(alias+' native money saved',(await rpc(c,'crm.lead','read',[[lead.id],['expected_revenue']]))[0].expected_revenue===1234567);
 }
 await button('Chuẩn bị hồ sơ');await p.getByRole('button',{name:'Chuẩn bị hồ sơ',exact:true}).waitFor({state:'hidden'});
 check(alias+' native prepare saved',(await rpc(c,'crm.lead','read',[[lead.id],['kd_bid_state']]))[0].kd_bid_state==='preparation');
 if(alias==='support'){check('support native submit absent',!await p.getByRole('button',{name:'Khai báo đã nộp',exact:true}).isVisible());}
 else{await button('Khai báo đã nộp');await p.getByRole('button',{name:'Khai báo đã nộp',exact:true}).waitFor({state:'hidden'});check(alias+' native submit saved',(await rpc(c,'crm.lead','read',[[lead.id],['kd_bid_state']]))[0].kd_bid_state==='submitted');}
 await shot(alias+'-native-create-flow');await c.close();
}
check('no browser errors',errors.length===0);check('source stable',JSON.stringify(sourceHashes())===JSON.stringify(initialHashes));ok=true;
}catch(e){if(p&&!p.isClosed()){await shot('native-flow-failure');fs.writeFileSync(path.join(out,'native-flow-failure.txt'),await p.locator('body').innerText());}errors.push(e.stack);}finally{await b.close();fs.writeFileSync(path.join(out,'native-flows.json'),JSON.stringify({ok,passed:checks.length,checks,errors,records,source_hashes:initialHashes},null,2));console.log(JSON.stringify({ok,passed:checks.length,errors:errors.length}));process.exitCode=ok?0:1;}})();
