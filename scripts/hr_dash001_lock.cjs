const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:18079',db='tp_tanphat_test',out=path.join(root,'.local/hr-dash001/lock-e2e');
fs.mkdirSync(out,{recursive:true});
const secret=JSON.parse(fs.readFileSync(path.join(root,'.local/dev-secrets.json')));
(async()=>{
 const browser=await chromium.launch({headless:true});const admin=await browser.newContext({viewport:{width:1280,height:1000}});
 const page=await admin.newPage();let employee,user;
 const checks=[];
 const rpc=async(model,method,args=[],kwargs={})=>{
  const r=await admin.request.post(base+'/web/dataset/call_kw/'+model+'/'+method,{data:{jsonrpc:'2.0',method:'call',params:{model,method,args,kwargs}}});
  const d=await r.json();assert(!d.error,d.error?.data?.message);return d.result;
 };
 const auth=async(ctx,login,password)=>{const r=await ctx.request.post(base+'/web/session/authenticate',{data:{jsonrpc:'2.0',method:'call',params:{db,login,password}}});return r.json();};
 const password=crypto.randomBytes(24).toString('base64url'),login='hrdash.e2e.'+Date.now();
 try {
  assert((await auth(admin,'admin',secret.admin)).result.uid);
  const session=await (await admin.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{}}})).json();
  const company=session.result.user_companies.current_company;
  const rows=await rpc('ir.model.data','search_read',[[['module','=','base'],['name','=','group_user']],['res_id']]);
  user=(await rpc('res.users','create',[[{name:'Synthetic lock E2E',login,password,company_id:company,company_ids:[[6,0,[company]]],group_ids:[[6,0,[rows[0].res_id]]]}]]))[0];
  const employees=await rpc('hr.employee','create',[[{name:'Synthetic lock E2E',company_id:company,user_id:user}]]);employee=employees[0];
  const actor=await browser.newContext();assert((await auth(actor,login,password)).result.uid);
  await page.goto(base+'/odoo/tp-hr');await page.locator('.o_tp_hr_kpis').waitFor({timeout:90000});
  const action=await rpc('hr.employee','action_open_account_dialog',[[employee]]);
  await page.evaluate(action=>odoo.__WOWL_DEBUG__.root.env.services.action.doAction(action),action);
  await page.locator('.modal .o_tp_hr_account_dialog').waitFor();
  await page.locator('.modal [name=reason] input').fill('Synthetic browser locking verification');
  await page.locator('.modal button[name=action_lock]').click();
  await page.getByRole('button',{name:'Ok',exact:true}).click();
  await page.locator('.o_tp_hr_account_dialog').waitFor({state:'detached'});
  const emp=await rpc('hr.employee','read',[[employee],['active','tp_account_status','user_id']]);
  assert.equal(emp[0].active,true);assert.equal(emp[0].tp_account_status,'disabled');
  checks.push('Admin native UI locks user without archiving employee');
  const locked=await auth(await browser.newContext(),login,password);assert(locked.error);assert(locked.error.data.message.includes('Tài khoản đã bị khóa'));
  const wrong=await auth(await browser.newContext(),login,'wrong-synthetic');assert(wrong.error);assert(!wrong.error.data.message.includes('Tài khoản đã bị khóa'));
  const invalid=await actor.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{}}});assert((await invalid.json()).error);
  checks.push('Correct password gets lock notice; wrong password generic; existing session rejected');
  const feedbackContext=await browser.newContext(),feedback=await feedbackContext.newPage();
  await feedback.goto(base+'/web/login?db='+db);await feedback.locator('[name=login]').fill(login);await feedback.locator('[name=password]').fill(password);await feedback.locator('button[type=submit]').click();
  await feedback.getByText('Tài khoản đã bị khóa, vui lòng gửi phản hồi',{exact:true}).waitFor();
  let requests=0;feedback.on('request',()=>requests++);
  await feedback.locator('.tp-auth-feedback summary').click();
  assert(await feedback.getByText('Tính năng gửi phản hồi đang phát triển.',{exact:true}).isVisible());
  assert.equal(requests,0);await feedback.screenshot({path:path.join(out,'locked-login.png')});
  checks.push('Feedback disclosure is keyboard/native UI only; no network or submission');
  const open=await rpc('hr.employee','action_open_account_dialog',[[employee]]);
  await page.evaluate(action=>odoo.__WOWL_DEBUG__.root.env.services.action.doAction(action),open);
  await page.locator('.modal [name=reason] input').fill('Synthetic browser unlocking verification');
  await page.locator('.modal button[name=action_unlock]').click();await page.getByRole('button',{name:'Ok',exact:true}).click();
  await page.locator('.o_tp_hr_account_dialog').waitFor({state:'detached'});
  assert((await auth(await browser.newContext(),login,password)).result.uid);
  checks.push('Unlock via native dialog restores login using same password');
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({ok:true,checks},null,2));
  console.log(JSON.stringify({ok:true,checks}));
 } catch(e){await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});fs.writeFileSync(path.join(out,'failure.txt'),e.stack);throw e;}
 finally {try {if(employee)await rpc('hr.employee','write',[[employee],{active:false,user_id:false}]);if(user)await rpc('res.users','unlink',[[user]]);}finally{await browser.close();}}
})().catch(e=>{console.error(e.message);process.exitCode=1;});

