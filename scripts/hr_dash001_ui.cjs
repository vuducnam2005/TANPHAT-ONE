const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),port=process.env.PORT||'18079',db=port==='18079'?'tp_tanphat_test':'tp_tanphat_dev';
assert(['18079','18069'].includes(port));
const base='http://127.0.0.1:'+port,out=path.join(root,process.env.HR_EVIDENCE_DIR||'.local/hr-dash001','ui-'+port);
fs.mkdirSync(out,{recursive:true});
const secret=JSON.parse(fs.readFileSync(path.join(root,'.local/dev-secrets.json')));
(async()=>{
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1100},acceptDownloads:true});
 const page=await context.newPage(),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 const check=async(name,fn)=>{await fn();checks.push(name);console.log('PASS '+name);};
 const rpc=async(method,args=[])=>{
  const r=await context.request.post(base+'/web/dataset/call_kw/tp.hr.workspace/'+method,{data:{jsonrpc:'2.0',method:'call',params:{model:'tp.hr.workspace',method,args,kwargs:{}}}});
  const data=await r.json();assert(!data.error,data.error?.data?.message);return data.result;
 };
 const overview=async()=>{await page.goto(base+'/odoo/tp-hr');await page.locator('.o_tp_hr_donut_total').waitFor({timeout:60000});};
 try {
 await page.goto(base+'/web/login?db='+db);await page.locator('[name=login]').fill('admin');
 await page.locator('[name=password]').fill(secret.admin);await page.locator('button[type=submit]').click();
 await page.locator('.o_web_client').waitFor({timeout:120000});await overview();
 const data=await rpc('get_overview');
 await check('5 KPI, shared department/job population and account partitions',async()=>{
  assert.equal(await page.locator('.o_tp_hr_kpis > *').count(),5);
  assert.equal(Number(await page.locator('.o_tp_hr_donut_total').textContent()),data.total);
  assert.equal(data.departments.reduce((sum,row)=>sum+row.count,0),data.total);
  assert.equal(data.jobs.reduce((sum,row)=>sum+row.count,0),data.total);
  assert.equal(data.linked+data.pending,data.total);assert.equal(data.complete_basic+data.missing_basic,data.total);
  assert.equal(await page.locator('.o_main_navbar').count(),1);
  await page.screenshot({path:path.join(out,'overview-1440.png'),fullPage:true});
 });
 await check('job filter, full export and reset retain catalog',async()=>{
  const job=data.catalog_jobs.find(row=>data.jobs.some(j=>j.id===row.id));assert(job);
  await page.getByLabel('Lọc chức vụ',{exact:true}).selectOption(String(job.id));
  await page.waitForFunction(()=>document.querySelector('.o_tp_hr_overview')?.getAttribute('aria-busy')!=='true');
  const filtered=await rpc('get_overview',[{job_id:job.id}]);
  assert.equal(Number(await page.locator('.o_tp_hr_donut_total').textContent()),filtered.total);
  const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Xuất Excel',exact:true}).click()]);
  await download.saveAs(path.join(out,'job-filter.xlsx'));
  const {execFileSync}=require('node:child_process');
  execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c',"import sys,openpyxl; w=openpyxl.load_workbook(sys.argv[1],read_only=True,data_only=True); s=w['Danh sách nhân viên']; rows=[r for r in s.iter_rows(min_row=6,values_only=True) if r[1]]; assert len(rows)==int(sys.argv[2]); assert all(r[4]==sys.argv[3] for r in rows); assert 'Chức vụ:' in s['A2'].value; print('XLSX PARITY PASS')",path.join(out,'job-filter.xlsx'),String(filtered.total),job.name],{encoding:'utf8'});
  await page.getByRole('button',{name:'Xóa bộ lọc',exact:true}).click();
  await page.waitForFunction(expected=>Number(document.querySelector('.o_tp_hr_donut_total')?.textContent)===expected,data.total);
  assert.equal(await page.getByLabel('Lọc chức vụ',{exact:true}).inputValue(),'');
 });
 await check('legend and job drilldowns use scoped native list; back retains dashboard',async()=>{
  await page.locator('.o_tp_hr_legend button').first().click();
  await page.locator('.o_list_view').waitFor();assert(await page.locator('.o_group_header').count());
  await page.goBack();await page.locator('.o_tp_hr_donut_total').waitFor();
  await page.locator('.o_tp_hr_bar button').first().click();await page.locator('.o_list_view').waitFor();
  await overview();
 });
 await check('responsive5 widths and mobile actions, dark/reduced motion and zoom200',async()=>{
  for(const width of [1440,1024,768,390,320]){
   await page.setViewportSize({width,height:1100});await page.waitForTimeout(150);
   const layout=await page.locator('.o_tp_hr_overview').evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}));
   assert(layout.scroll<=layout.client+1,'dashboard overflow at '+width+': '+JSON.stringify(layout));
   assert(await page.getByRole('button',{name:'Xuất Excel',exact:true}).isVisible());
   await page.screenshot({path:path.join(out,'overview-'+width+'.png'),fullPage:false});
  }
  await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
  const palette=await page.locator('.o_tp_hr_overview').evaluate(el=>({surface:getComputedStyle(el).getPropertyValue('--hr-surface').trim(),motion:getComputedStyle(el.querySelector('button')).transitionDuration}));
  assert.equal(palette.surface,'#fff');assert.equal(palette.motion,'0s');
  await page.screenshot({path:path.join(out,'overview-dark-320.png')});
  await page.emulateMedia({colorScheme:'light',reducedMotion:'no-preference'});
  await page.setViewportSize({width:1440,height:1100});
  await page.evaluate(()=>{document.body.style.zoom='2';});
  const layout=await page.locator('.o_tp_hr_overview').evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}));
  assert(layout.scroll<=layout.client+1,'zoom200 overflow');
  await page.screenshot({path:path.join(out,'overview-zoom200.png')});
  await page.evaluate(()=>{document.body.style.zoom='';});
 });
 await check('employee list status column, grouped roster and read-only account dialog',async()=>{
  await overview();await page.locator('.o_tp_hr_sidebar').getByRole('link',{name:'Danh sách nhân viên',exact:true}).click();
  await page.locator('.o_list_view').waitFor();
  assert.equal(await page.locator('th[data-name=active]').count(),0);
  assert.equal((await page.locator('th[data-name=tp_account_status]').textContent()).trim(),'Tình trạng');
  assert.equal(await page.locator('.o_searchview_facet').count(),0);
  assert(await page.locator('.o_group_header').count()>0);
  const row=page.locator('.o_data_row').filter({hasText:'kd.thuyanh'}).first();
  if(await row.count()){await row.locator('button[name=action_open_account_dialog]').click();
   await page.locator('.modal .o_tp_hr_account_dialog').waitFor();
   assert(await page.locator('.modal button[name=action_lock]').isVisible());
   await page.screenshot({path:path.join(out,'account-dialog.png')});
   await page.getByRole('button',{name:'Đóng',exact:true}).last().click();
  }
 });
 assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({ok:true,port,checks,total:data.total,units:data.units,linked:data.linked,pageerrors:errors},null,2));
 } catch(error){fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({ok:false,port,checks,error:error.stack,pageerrors:errors},null,2));await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});throw error;}
 finally {await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});

