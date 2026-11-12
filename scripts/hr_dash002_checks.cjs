const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),port=process.env.PORT||'18079';
assert(['18079','18069'].includes(port));
const base=`http://${port==='18079'?'localhost':'127.0.0.1'}:${port}`,db=port==='18079'?'tp_tanphat_test':'tp_tanphat_dev';
const out=path.join(root,'.local/hr-dash002/checks-'+port);fs.mkdirSync(out,{recursive:true});
const secret=JSON.parse(fs.readFileSync(path.join(root,'.local/dev-secrets.json')));
(async()=>{const b=await chromium.launch({headless:true}),c=await b.newContext({viewport:{width:1440,height:1100},acceptDownloads:true});
const p=await c.newPage(),errors=[],consoleErrors=[],checks=[];
p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
const check=async(name,fn)=>{await fn();checks.push(name);console.log('PASS '+name);};
const ready=async()=>p.locator('.o_tp_hr_donut_total').waitFor({timeout:90000});
const overview=async()=>{await p.goto(base+'/odoo/tp-hr');await ready();};
const loaded=async()=>p.waitForFunction(()=>document.querySelector('.o_tp_hr_overview')?.getAttribute('aria-busy')!=='true');
const loadAction=async fn=>{const response=p.waitForResponse(r=>r.url().includes('/get_overview'));await fn();await response;await loaded();};
const reset=async()=>loadAction(()=>p.locator('.o_tp_hr_filters button').click());
try{
 await p.goto(base+'/web/login?db='+db);await p.locator('[name=login]').fill('admin');await p.locator('[name=password]').fill(secret.admin);await p.locator('button[type=submit]').click();await p.locator('.o_web_client').waitFor({timeout:120000});await overview();
 const r=await c.request.post(base+'/web/dataset/call_kw/tp.hr.workspace/get_overview',{data:{jsonrpc:'2.0',method:'call',params:{model:'tp.hr.workspace',method:'get_overview',args:[],kwargs:{}}}});const data=(await r.json()).result;assert(data);
 await check('large donut, distinct catalog colors, all jobs visible on common zero scale',async()=>{
  const box=await p.locator('.o_tp_hr_donut').boundingBox();assert(box.width>=260&&box.width<=320);
  const colors=await p.locator('.o_tp_hr_donut path').evaluateAll(es=>es.map(e=>e.getAttribute('fill')));assert.equal(new Set(colors).size,data.departments.length);
  assert.equal(await p.locator('.o_tp_hr_bar').count(),data.jobs.length);
  assert(await p.locator('.o_tp_hr_job_bars').evaluate(e=>e.scrollHeight<=e.clientHeight+1));
  const heights=await p.locator('.o_tp_hr_bar_track').evaluateAll(es=>es.map(e=>e.getBoundingClientRect().height));assert(heights.every(v=>v>=14&&v<=22));
  assert.equal((await p.locator('.o_tp_hr_bar_axis span').first().textContent()).trim(),'0');
  assert.equal(Number(await p.locator('.o_tp_hr_donut_total').textContent()),data.total);
  await p.screenshot({path:path.join(out,'desktop.png')});
  const colorsByName=await p.locator('.o_tp_hr_legend button').evaluateAll(es=>Object.fromEntries(es.map(e=>[e.children[1].textContent,getComputedStyle(e.children[0]).backgroundColor])));
  await loadAction(()=>p.getByLabel('Lọc đơn vị',{exact:true}).selectOption(String(data.departments[0].id)));await p.waitForFunction(()=>document.querySelectorAll('.o_tp_hr_legend button').length===1);
  assert.equal(await p.locator('.o_tp_hr_legend .o_tp_hr_dot').evaluate(e=>getComputedStyle(e).backgroundColor),colorsByName[data.departments[0].name]);
  await reset();
 });
 await check('hover and keyboard tooltip highlight, Escape and correct slice drilldown',async()=>{
  const legend=p.locator('.o_tp_hr_legend button').first();await legend.hover();
  await p.locator('[role=tooltip]').waitFor();assert.equal(await p.locator('.o_tp_hr_donut path.is-highlighted').count(),1);
  const tip=await p.locator('[role=tooltip]').innerText();assert(tip.includes(data.departments[0].name)&&tip.includes(String(data.departments[0].count))&&tip.includes('%'));
  const tipBox=await p.locator('[role=tooltip]').boundingBox();assert(tipBox.x>=0&&tipBox.x+tipBox.width<=1440&&tipBox.y>=0&&tipBox.y+tipBox.height<=1100);
  await p.mouse.move(1430,1080);const slice=p.locator('.o_tp_hr_donut path').first();await slice.focus();await p.locator('[role=tooltip]').waitFor();await p.keyboard.press('Escape');await p.locator('[role=tooltip]').waitFor({state:'hidden'});assert.equal(await p.locator('[role=tooltip]').count(),0);
  const response=p.waitForResponse(r=>r.url().includes('/action_employees'));
  await p.keyboard.press('Space');const actionResponse=await response;assert.deepEqual(actionResponse.request().postDataJSON().params.args[1],[['department_id','=',data.departments[0].id]]);
  await p.locator('.o_list_view').waitFor();await overview();
  await p.locator('.o_tp_hr_bar button').first().focus();await p.locator('[role=tooltip]').waitFor();assert((await p.locator('[role=tooltip]').innerText()).includes(data.jobs[0].name));
 });
 await check('table search stays local, account subcounts and read-only drilldown',async()=>{
  const total=await p.locator('.o_tp_hr_donut_total').textContent();await p.getByLabel('Tìm đơn vị trong bảng',{exact:true}).fill('not-a-real-unit');await p.waitForFunction(()=>document.querySelectorAll('.o_tp_hr_summary tbody tr').length===0);assert.equal(await p.locator('.o_tp_hr_summary tbody tr').count(),0);assert.equal(await p.locator('.o_tp_hr_donut_total').textContent(),total);
  await p.getByLabel('Tìm đơn vị trong bảng',{exact:true}).fill('');for(const size of ['10','20','50','100'])await p.getByLabel('Số dòng tổng hợp',{exact:true}).selectOption(size);
  assert((await p.locator('.o_tp_hr_account_states').innerText()).includes('Trong số đã liên kết'));
  const response=p.waitForResponse(r=>r.url().includes('/action_employees'));
  await p.locator('.o_tp_hr_account_open').click();const res=await response;assert.deepEqual(res.request().postDataJSON().params.args[1],[['tp_account_status','=','active']]);await p.locator('.o_list_view').waitFor();await overview();
 });
 await check('employee profile and account status dialog remain available read-only',async()=>{
  await p.locator('.o_tp_hr_kpis button').first().click();await p.locator('.o_list_view').waitFor();
  await p.locator('.o_data_row td[name=name]').first().click();await p.locator('.o_tp_hr_employee_form').waitFor();
  assert.equal(await p.locator('.o_tp_hr_employee_form .o_notebook_headers .nav-item').count(),6);
  await p.locator('.o_tp_hr_employee_form button[name=action_open_account_dialog]').click();await p.locator('.o_tp_hr_account_dialog').waitFor();
  await p.getByRole('button',{name:'Đóng',exact:true}).last().click();await overview();
 });
 await check('empty keeps catalogs; network error exposes retry and recovers',async()=>{
  const route='**/web/dataset/call_kw/tp.hr.workspace/get_overview*';
  await p.route(route,async route=>route.fulfill({json:{jsonrpc:'2.0',result:{...data,total:0,units:0,linked:0,pending:0,departments:[],jobs:[]}}}));
  await loadAction(()=>p.getByRole('button',{name:'Làm mới',exact:true}).click());assert.equal(await p.locator('.o_tp_hr_charts').count(),0);assert.equal(await p.getByLabel('Lọc đơn vị',{exact:true}).locator('option').count(),data.catalog_departments.length+1);
  await p.unroute(route);await reset();
  await p.route(route,async route=>route.fulfill({json:{jsonrpc:'2.0',error:{code:200,message:'test-only injected failure',data:{name:'Error',message:'offline'}}}}));
  await p.getByRole('button',{name:'Làm mới',exact:true}).click();await p.locator('.o_tp_hr_message[role=alert]').waitFor();assert(await p.getByRole('button',{name:'Xuất Excel',exact:true}).isDisabled());
  await p.unroute(route);await p.getByRole('button',{name:'Thử lại',exact:true}).click();await ready();
 });
 await check('OS dark plus real Odoo dark CSS keeps HR light, input and tooltip readable',async()=>{
  await p.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
  await p.addStyleTag({url:base+'/web/assets/debug/web.assets_web_dark.css'});
  await p.evaluate(()=>{document.documentElement.dataset.bsTheme='dark';document.body.classList.add('o_dark','o_tp_dark');});
  const palette=await p.locator('.o_tp_hr_overview').evaluate(e=>{const style=getComputedStyle(e),section=getComputedStyle(e.querySelector('section')),input=getComputedStyle(e.querySelector('select'));return {bg:style.backgroundColor,text:style.color,section:section.backgroundColor,input:input.backgroundColor,scheme:style.colorScheme};});
  assert.deepEqual(palette,{bg:'rgb(244, 247, 251)',text:'rgb(30, 41, 59)',section:'rgb(255, 255, 255)',input:'rgb(255, 255, 255)',scheme:'light'});
  assert.equal(await p.locator('.o_tp_hr_sidebar').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(23, 50, 77)');
  await p.locator('.o_tp_hr_legend button').first().focus();assert.equal(await p.locator('[role=tooltip]').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(255, 255, 255)');
  await p.screenshot({path:path.join(out,'odoo-dark-light-hr.png')});await overview();
 });
 await check('touch390, drawer and readable mobile chart without page overflow',async()=>{
  const mobile=await b.newContext({viewport:{width:390,height:1100},isMobile:true,hasTouch:true,storageState:await c.storageState()}),m=await mobile.newPage();
  m.on('pageerror',e=>errors.push(e.message));await m.goto(base+'/odoo/tp-hr');await m.locator('.o_tp_hr_donut_total').waitFor();
  await m.getByRole('button',{name:'Menu TP HR',exact:true}).tap();await m.locator('.o_tp_hr_sidebar.is-drawer').waitFor();await m.getByRole('button',{name:'Đóng menu',exact:true}).tap();
  await m.locator('.o_tp_hr_structure').scrollIntoViewIfNeeded();await m.screenshot({path:path.join(out,'mobile-chart.png')});
  const layout=await m.locator('.o_tp_hr_overview').evaluate(e=>({width:e.clientWidth,scroll:e.scrollWidth}));assert(layout.scroll<=layout.width+1);
  await m.locator('.o_tp_hr_legend button').first().tap();await m.locator('.o_list_view').waitFor();await mobile.close();
 });
 assert.deepEqual(errors,[]);assert.deepEqual(consoleErrors,[]);
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({ok:true,checks,pageerrors:errors,consoleErrors},null,2));
}catch(e){fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({ok:false,checks,error:e.stack,pageerrors:errors,consoleErrors},null,2));await p.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});throw e;}finally{await b.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
