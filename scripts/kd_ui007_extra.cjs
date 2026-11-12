/* Related forms, smart buttons and native saved filters. Writes are clone-only UI preferences. */
module.exports = async function(ctx) {
 const {browser,base,target,login,ok,watch,settle,shot,check,openList,openFirst}=ctx;
 async function closeModal(p){await p.locator('.modal').last().locator('.modal-footer,footer').getByRole('button',{name:/^(Đóng|Hủy|Bỏ qua)$/}).first().click();await settle(p);}
 async function related(p,scope,name){
  const rel=scope.locator(`[name="${name}"]`).first(),tool=rel.locator('.tp_kd_relation_tools');
  check(`${name} relation controls visible`,await tool.isVisible());
  check(`${name} four related page lengths`,await rel.getByLabel('Số dòng bảng con').locator('option').count()===4);
  const button=tool.locator('.tp_kd_relation_filter');
  if(await button.isEnabled()){
   await rel.getByLabel('Số dòng bảng con').selectOption('10');await settle(p);
   check(`${name} native relation at most10`,await rel.locator('.o_data_row').count()<=10);
   await button.click();await p.locator('.tp_kd_relation_dialog .tp_kd_filter_bar').waitFor();await settle(p);
   const dialog=p.locator('.tp_kd_relation_dialog');
   check(`${name} readonly dialog has real filters`,await dialog.getByLabel('Trường lọc',{exact:true}).locator('option').count()>0);
   check(`${name} dialog readonly`,await dialog.locator('.o_list_button_add,.o_list_record_remove,.o_field_x2many_list_row_add').count()===0);
   await shot(p,`extra-${name}-${Date.now()}`);
   await closeModal(p);
  } else check(`${name} unsaved explains disabled`,(await tool.innerText()).includes('Lưu thay đổi để lọc'));
 }
 const c=await login(browser,'editor'),p=await c.newPage();watch(p);
 // Each typed event popup uses the explicit readonly form and the granted snapshot table.
 for(const [leaf,model] of [['allocations','tp.allocation'],['productions','tp.production'],['acceptances','tp.acceptance'],['payments','tp.payment.request'],['plans','tp.periodic.plan'],['credentials','tp.credential'],['obligations','tp.obligation']]){
  const a=ctx.LEAVES.find(([name])=>name===leaf)[1];
  await openList(p,a);
  const snapshots=['tp.allocation','tp.production','tp.acceptance','tp.payment.request','tp.periodic.plan'].includes(model)
   ? await ok(c,`${model}.event`,'search_read',[[['amount_ids','!=',false]],['record_id']],{limit:1}):[];
  const records=snapshots.length?[{id:snapshots[0].record_id[0]}]:await ok(c,model,'search_read',[[['event_ids','!=',false]],['id']],{limit:1});
  check(`${leaf} event fixture available`,records.length===1);
  if(!records.length)continue;
  await p.goto(`${base}/odoo/action-${a}/${records[0].id}`);await p.locator('.o_form_view').first().waitFor();await settle(p);
  await p.getByRole('tab',{name:'Lịch sử lần trình',exact:true}).click();await settle(p);
  await related(p,p.locator('.o_action_manager'),'event_ids');
  const eventRows=p.locator('[name="event_ids"] .o_data_row');
  await (snapshots.length?eventRows.filter({hasText:'submit'}):eventRows).first().locator('.o_data_cell').first().click();await p.locator('.modal .o_form_view').waitFor();await settle(p);
  check(`${leaf} history readonly`,await p.locator('.modal .o_form_button_save').count()===0);
  check(`${leaf} history datetime shows year`,/\b20\d\d\b/.test(await p.locator('.modal [name="acted_at"]').innerText()));
  const amount=p.locator('.modal [name="amount_ids"]');
  if(await amount.isVisible())await related(p,p.locator('.modal').last(),'amount_ids');
  await shot(p,`event-${leaf}-1440`);await closeModal(p);
 }
 await openList(p,'tp_contract.action_tp_contracts');await openFirst(p);
 for(const method of ['action_tp_open_documents','action_tp_open_audit']){
  await p.locator(`button[name="${method}"]`).click();await p.locator('.o_list_view').waitFor();await settle(p);
  check(`${method} native filtered/paged table`,await p.locator('.tp_kd_filter_bar').isVisible()&&await p.getByLabel('Số dòng mỗi trang',{exact:true}).isVisible());
  check(`${method} readonly create guard`,await p.locator('.o_list_button_add').count()===0);
  await shot(p,`smart-${method}-1440`);
  await openList(p,'tp_contract.action_tp_contracts');await openFirst(p);
 }
 await p.locator('[name="revision_ids"] .o_data_row .o_data_cell').first().click();await p.locator('.modal .o_form_view').waitFor();await settle(p);
 for(const [tab,name] of [['Dòng phạm vi','line_ids'],['Lần trình rà soát','submission_ids'],['Tham chiếu BASE','approval_reference_ids']]){
  await p.locator('.modal').last().getByRole('tab',{name:tab,exact:true}).click();await settle(p);await related(p,p.locator('.modal').last(),name);
  await shot(p,`revision-${name}-1440`);
 }
 const money=p.locator('.modal button[name="action_tp_open_amounts"]');
 if(await money.isVisible()){
  await money.click();await p.locator('.o_list_view').waitFor();await settle(p);
  check('contract money smart table real filter pager',await p.locator('.tp_kd_filter_bar').isVisible());await shot(p,'smart-amounts-1440');
 } else await closeModal(p);
 await c.close();
 if(target==='clone') {
  const r=await login(browser,'reviewer'),rp=await r.newPage();watch(rp);
  await openList(rp,'tp_contract.action_tp_contracts');
  const versions=await ok(r,'tp.contract.revision','search_read',[[['review_state','=','in_review']],['tp_can_return_review','contract_id','name']],{limit:100});
  const version=versions.find(v=>v.tp_can_return_review);check('reviewer return wizard fixture available',Boolean(version));
  if(version){
   const contract=await ok(r,'tp.contract','read',[[version.contract_id[0]]],{fields:['code']});
   await rp.getByLabel('Trường lọc',{exact:true}).selectOption('code');
   const code=rp.locator('input[aria-label="Giá trị lọc"]');await code.waitFor();await code.fill(contract[0].code);await code.press('Enter');await settle(rp);await openFirst(rp);
   await rp.locator('[name="revision_ids"] .o_data_row').filter({hasText:version.name}).first().locator('.o_data_cell').first().click();await rp.locator('.modal .o_form_view').waitFor();await settle(rp);
   await rp.locator('.modal').last().getByRole('button',{name:'Trả lại để chỉnh sửa',exact:true}).click();await rp.locator('.modal [name="issue_ids"]').waitFor();await settle(rp);
   const issues=rp.locator('.modal').last().locator('[name="issue_ids"]');
   check('return wizard unsaved relation has visible disabled filter',await issues.locator('.tp_kd_relation_filter').isDisabled());
   check('return wizard explains saving before filtering',(await issues.innerText()).includes('Lưu thay đổi để lọc'));
   await shot(rp,'return-wizard-unsaved-1440');await closeModal(rp);
  }
  await r.close();
 }
 if(target==='clone') {
  const saved=await login(browser,'editor'),fp=await saved.newPage();watch(fp);
  await openList(fp,'tp_kd_workspace.action_opportunities');
  await fp.getByLabel('Trường lọc',{exact:true}).selectOption('name');await settle(fp);
  await fp.getByLabel('Giá trị lọc',{exact:true}).fill('UI007-PAGE-1');await fp.getByLabel('Giá trị lọc',{exact:true}).press('Enter');await settle(fp);
  await fp.locator('.tp_kd_advanced').click();await fp.locator('.o_add_favorite').click();
  const favName='UI007 saved '+Date.now();
  await fp.locator('.o_add_favorite + .o_accordion_values input[type="text"]').fill(favName);
  await fp.locator('.o_save_favorite').click();await settle(fp);
  await fp.locator('.tp_kd_clear_filters').click();await settle(fp);
  await fp.reload();await fp.locator('.tp_kd_filter_bar').waitFor();await settle(fp);
  await fp.locator('.tp_kd_advanced').click();await fp.getByRole('menuitemcheckbox',{name:favName,exact:true}).click();await settle(fp);
  check('saved native filter synchronizes facet and record count',await fp.locator('.o_searchview_facet').count()>0&&(await fp.locator('.o_pager_limit').innerText()).trim()==='18');
  await fp.locator('.o_searchview_facet .o_facet_remove').click();await settle(fp);
  check('removing saved chip clears selection without losing action scope',await fp.locator('.o_searchview_facet').count()===0);
  await fp.locator('.tp_kd_advanced').click();
  await fp.locator('.o-dropdown--menu').getByText('Tình trạng hồ sơ',{exact:true}).click();await settle(fp);
  check('grouped pager labels groups',await fp.locator('.tp_kd_page_size').innerText().then(t=>t.includes('nhóm mỗi trang')));
  await fp.getByLabel('Số dòng mỗi trang',{exact:true}).selectOption('10');await settle(fp);
  check('native group headers retained',await fp.locator('.o_group_header').count()>0);
  await shot(fp,'saved-and-grouped-1440');await saved.close();
 }
 // Manager-only project assignment table.
 const manager=await login(browser,'planner'),mp=await manager.newPage();watch(mp);
 await openList(mp,'tp_kd_workspace.action_projects');await openFirst(mp);
 await mp.getByRole('tab',{name:'Phân công',exact:true}).click();await settle(mp);
 await related(mp,mp.locator('.o_action_manager'),'tp_assignment_ids');await shot(mp,'project-assignments-1440');
 await manager.close();
 // No-money actor: opening event metadata must not fetch protected money fields.
 const metadata=await login(browser,'metadata'),np=await metadata.newPage();watch(np);const calls=[];
 np.on('request',r=>{if(r.url().includes('/web/dataset/call_kw/')){try{calls.push(r.postDataJSON()?.params);}catch{}}});
 await openList(np,'tp_kd_workspace.action_payments');await openFirst(np);
 await np.getByRole('tab',{name:'Lịch sử lần trình',exact:true}).click();await settle(np);
 if(await np.locator('[name="event_ids"] .o_data_row').count()){
  await np.locator('[name="event_ids"] .o_data_row .o_data_cell').first().click();await np.locator('.modal .o_form_view').waitFor();await settle(np);
  check('metadata event hides granted snapshot table',await np.locator('.modal [name="amount_ids"]').count()===0);
 }
 check('metadata no protected money RPC',!calls.some(r=>r.model?.endsWith('.amount')&&['read','web_read','web_search_read'].includes(r.method)),calls.map(r=>r.model));
 await metadata.close();
};
