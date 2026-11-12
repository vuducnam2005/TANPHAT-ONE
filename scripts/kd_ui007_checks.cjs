/* Full workspace browser coverage, including related tables. */
const fs = require('node:fs'),path=require('node:path');
module.exports=async function(ctx){
 const {browser,base,target,mode,local,login,ok,rpc,check,watch,settle,shot,openList,openFirst,LEAVES}=ctx;
 const c=await login(browser,'editor'),p=await c.newPage();watch(p);
 const requests=[];p.on('request',r=>{if(r.url().includes('/web/dataset/call_kw/')){try{requests.push(r.postDataJSON()?.params);}catch{}}});
 const isAfter=mode!=='probe';
 for(const [name,action] of mode==='deep'?[]:LEAVES){
  await openList(p,action);
  if(mode==='layout') {
   console.log(JSON.stringify(await p.evaluate(()=>[...document.querySelectorAll('.o_list_view,.o_control_panel,.o_control_panel_main,.o_control_panel_breadcrumbs,.o_control_panel_navigation,.o_control_panel_actions,.o_searchview,.tp_kd_filter_bar,.o_content')].map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {cls:e.className,rect:{x:r.x,y:r.y,w:r.width,h:r.height},display:s.display,flex:s.flex,dir:s.flexDirection,align:s.alignSelf,position:s.position,overflow:s.overflow,min:s.minHeight,max:s.maxHeight};}))));
   await shot(p,'layout');break;
  }
  if(!isAfter){await shot(p,`probe-${name}`);continue;}
  check(`${name} visible filters`,await p.locator('.tp_kd_filter_bar').isVisible());
  const size=p.getByLabel('Số dòng mỗi trang',{exact:true});
  check(`${name} four page sizes`,await size.locator('option').count()===4);
  await size.selectOption('10');await p.waitForFunction(()=>document.querySelectorAll('.o_data_row').length<=10);await settle(p);
  check(`${name} at most ten rows`,await p.locator('.o_data_row').count()<=10);
  const labels=await p.getByLabel('Trường lọc',{exact:true}).locator('option').allTextContents();
  check(`${name} model specific searchable fields`,labels.length>0,labels);
  const quick=p.locator('.tp_kd_quick_filter').first();
  if(await quick.count()){
   await quick.click();await settle(p);check(`${name} native facet after quick filter`,await p.locator('.o_searchview_facet').count()>0);
   await shot(p,`filtered-${name}-1440`);await p.locator('.tp_kd_clear_filters').click();await settle(p);
  }
  await shot(p,`list-${name}-1440`);
  if(await p.locator('.o_data_row').count()){
   await openFirst(p);await shot(p,`form-${name}-1440`,true);
   const tabs=p.locator('.o_notebook_headers .nav-link');
   for(let i=0;i<await tabs.count();i++){
    await tabs.nth(i).click();await settle(p);
    for(const tool of await p.locator('.tab-pane.active .tp_kd_relation_tools').all()) {
     check(`${name} related table labeled`,(await tool.innerText()).includes('dòng mỗi trang'));
     const b=tool.locator('.tp_kd_relation_filter');
     if(await b.isEnabled()){
      await b.click();await p.locator('.tp_kd_relation_dialog .tp_kd_filter_bar').waitFor({timeout:15000});await settle(p);
      check(`${name} related filter server table`,await p.locator('.tp_kd_relation_dialog .o_list_view').count()===1);
      await shot(p,`relation-${name}-${i}-1440`);
      await p.locator('.modal').last().locator('.modal-footer').getByRole('button',{name:'Đóng',exact:true}).click();await settle(p);
     }
    }
    await shot(p,`tab-${name}-${i}-1440`,true);
   }
  }
 }
 if(isAfter && mode!=='layout') {
  if(target==='clone') {
   await openList(p,'tp_kd_workspace.action_opportunities');
   const add=async(field,value)=>{
    await p.getByLabel('Trường lọc',{exact:true}).selectOption(field);await settle(p);
    const input=p.locator('input[aria-label="Giá trị lọc"]');
    await input.waitFor();await input.fill(value);await input.press('Enter');
    await settle(p);
   };
   await p.locator('.tp_kd_clear_filters').click();await settle(p);await add('name','UI007-PAGE-');
   const size=p.getByLabel('Số dòng mỗi trang',{exact:true});
   for(const n of [10,20,50,100]){
    requests.length=0;await size.selectOption(String(n));await p.waitForFunction(n=>document.querySelectorAll('.o_data_row').length===n,n);
    check(`118 records size ${n} real rows`,await p.locator('.o_data_row').count()===n);
    check(`118 records size ${n} server limit offset`,requests.some(r=>r.method==='web_search_read'&&r.kwargs.limit===n&&r.kwargs.offset===0),requests.map(r=>({method:r.method,limit:r.kwargs?.limit,offset:r.kwargs?.offset})));
   }
   requests.length=0;await p.locator('.o_pager_next').click();await p.waitForFunction(()=>document.querySelectorAll('.o_data_row').length===18);
   check('118 records page2 has remaining18',await p.locator('.o_data_row').count()===18);
   check('page2 server offset100',requests.some(r=>r.method==='web_search_read'&&r.kwargs.offset===100));
   await shot(p,'page2-opportunities-100');
   await p.locator('.tp_kd_clear_filters').click();await settle(p);await add('name','UI007-PAGE-1');await size.selectOption('10');await settle(p);
   check('18 records page1 ten',await p.locator('.o_data_row').count()===10);
   await p.locator('.o_pager_next').click();await p.waitForFunction(()=>document.querySelectorAll('.o_data_row').length===8);
   check('18 records page2 eight',await p.locator('.o_data_row').count()===8);await shot(p,'18-records-page2-eight');
   await add('name','DOES-NOT-EXIST');await settle(p);
   check('last page filtering empty returns offset0',await p.locator('.o_data_row').count()===0&&requests.filter(r=>r.method==='web_search_read').at(-1)?.kwargs.offset===0);
   await p.locator('.tp_kd_clear_filters').click();await settle(p);
   const fixture=JSON.parse(fs.readFileSync(path.join(local,'fixture.json')));
   await openList(p,'tp_kd_workspace.action_allocations');await p.getByLabel('Trường lọc',{exact:true}).selectOption('code');await p.locator('input[aria-label="Giá trị lọc"]').waitFor();await p.getByLabel('Giá trị lọc',{exact:true}).fill('UI007-PARENT');await p.getByLabel('Giá trị lọc',{exact:true}).press('Enter');await settle(p);await openFirst(p);
   await p.getByRole('tab',{name:'Khoán cấp 2',exact:true}).click();await settle(p);
   const relation=p.locator('[name="child_ids"]');await relation.getByLabel('Số dòng bảng con').selectOption('10');await settle(p);
   check('relation18 first page10',await relation.locator('.o_data_row').count()===10);
   await relation.locator('.o_pager_next').click();await settle(p);check('relation18 page2 eight',await relation.locator('.o_data_row').count()===8);
   await relation.locator('.tp_kd_relation_filter').click();await p.locator('.tp_kd_relation_dialog .tp_kd_filter_bar').waitFor();await settle(p);
   await p.locator('.tp_kd_relation_dialog').getByLabel('Trường lọc',{exact:true}).selectOption('name');
   const find=p.locator('.tp_kd_relation_dialog input[aria-label="Giá trị lọc"]');await find.waitFor();await find.fill('Khoán con 00');await find.press('Enter');await settle(p);
   check('related filter searches full relation beyond current page',await p.locator('.tp_kd_relation_dialog .o_data_row').count()===1);
   await p.locator('.modal-footer').last().getByRole('button',{name:'Đóng',exact:true}).click();
   const rows=await ok(c,'tp.allocation','read',[[fixture.allocation]],{fields:['child_ids']});
   check('filter leaves full18 relation unchanged',rows[0].child_ids.length===18);
   await shot(p,'relation18-page2');
  }
  for(const width of [1920,768,390,360]) {
   await p.setViewportSize({width,height:1000});
   for(const [name,a] of LEAVES) {
    await openList(p,a);
    const layout=await p.evaluate(()=>({overflow:document.documentElement.scrollWidth-innerWidth,filter:document.querySelector('.tp_kd_filter_bar')?.getBoundingClientRect().bottom,content:document.querySelector('.o_content')?.getBoundingClientRect().top}));
    check(`${name}@${width} no page overflow`,layout.overflow<=1,layout);
    check(`${name}@${width} filter above content`,layout.filter<=layout.content+1,layout);
    check(`${name}@${width} single visible native search`,await p.getByRole('searchbox').count()===1&&await p.getByRole('searchbox').isVisible());
    await shot(p,`list-${name}-${width}`);
    if(width===390&&await p.locator('.o_data_row').count()){await openFirst(p);await shot(p,`form-${name}-${width}`,true);}
   }
  }
  await p.setViewportSize({width:1440,height:1000});
  await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`,{timeout:120000});await p.locator('.o_tp_kd_ov').waitFor();await settle(p);
  const overviewSelect=p.locator('.o_tp_kd_pager select').first();
  for(const n of [10,20,50,100]){requests.length=0;await overviewSelect.selectOption(String(n));await settle(p);check(`overview page size${n} sent`,requests.some(r=>r.method==='get_kd_project_rows'&&r.args[4]===n));}
  await shot(p,'overview-1440',true);
  const sources=p.locator('.o_tp_kd_sources .o_tp_kd_disclosure');
  if(await sources.getAttribute('aria-expanded')!=='true')await sources.click();
  await p.locator('.o_tp_kd_sources .o_tp_kd_hint').first().waitFor();await settle(p);await shot(p,'sources-fixed-1440',true);
  check('sources fixed rows label',await p.locator('.o_tp_kd_sources').innerText().then(t=>t.includes('nhóm nguồn cố định')));
  const planFull=p.locator('.tp_kd_plan_full');await planFull.waitFor();await planFull.click();await p.locator('.o_list_view .o_list_renderer').waitFor();await settle(p);
  check('plan comparison has full native filtered/paged drilldown',await p.locator('.tp_kd_filter_bar').isVisible());await shot(p,'overview-plan-full-list');
  await p.goto(`${base}/odoo/action-tp_kd_workspace.action_overview`);await p.locator('.o_tp_kd_ov').waitFor();await settle(p);
  await p.locator('.o_tp_kd_detail [role="tab"]').last().click();await p.locator('.o_tp_kd_cred').waitFor();await settle(p);
  const credFull=p.locator('.tp_kd_cred_full');
  if(await credFull.count()){
   await credFull.click();await p.locator('.o_list_view .o_list_renderer').waitFor();await settle(p);
   check('credential nearest-five opens all matching scoped records',await p.locator('.tp_kd_filter_bar').isVisible());await shot(p,'overview-credential-full-list');
  }
 }
 fs.writeFileSync(path.join(ctx.out,'rpc-evidence.json'),JSON.stringify(requests.map(r=>({model:r.model,method:r.method,limit:r.kwargs?.limit,offset:r.kwargs?.offset})),null,2));
 await c.close();
 if(['after','verify','extra'].includes(mode))await require('./kd_ui007_extra.cjs')(ctx);
};
